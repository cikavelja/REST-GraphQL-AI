from fastapi import FastAPI, Depends, HTTPException
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import Column, Integer, String, Text, ForeignKey, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import strawberry
import jwt
import bcrypt
from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
import json

# Load Local Embedding Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast & lightweight model

# Database Configuration
DATABASE_URL = "postgresql+asyncpg://admin:admin123@127.0.0.1:5432/gqlpy"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# Authentication Configuration
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        async with get_db_session() as db:
            result = await db.execute(select(User).filter(User.username == payload.get("sub")))
            user = result.scalar_one_or_none()
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")

# Category Model
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    articles = relationship("Article", back_populates="category")

# Article Model
class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    vector = Column(Text)
    search_text = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="articles")

# Async Database Dependency
@asynccontextmanager
async def get_db_session():
    async with SessionLocal() as session:
        yield session

# GraphQL Types
@strawberry.type
class CategoryType:
    id: int
    name: str

@strawberry.type
class ArticleType:
    id: int
    title: str
    content: str
    category: Optional[CategoryType]

@strawberry.type
class UserType:
    id: int
    username: str
    role: str

@strawberry.type
class Query:
    @strawberry.field
    async def list_articles(self, info) -> List[ArticleType]:
        db: AsyncSession = info.context["db"]
        result = await db.execute(select(Article))
        return result.scalars().all()

    @strawberry.field
    async def get_article(self, info, id: int) -> Optional[ArticleType]:
        db: AsyncSession = info.context["db"]
        result = await db.execute(select(Article).filter(Article.id == id))
        return result.scalar_one_or_none()
    
    @strawberry.field
    async def list_categories(self, info) -> List[CategoryType]:
        db: AsyncSession = info.context["db"]
        result = await db.execute(select(Category))
        return result.scalars().all()
    
    @strawberry.field
    async def protected_info(self, info, user: UserType = Depends(get_current_user)) -> str:
        return f"Protected data for {user.username}"

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_article(self, info, title: str, content: str, category_id: int) -> ArticleType:
        db: AsyncSession = info.context["db"]
        embedding_vector = embedding_model.encode(content).tolist()
        article = Article(title=title, content=content, vector=json.dumps(embedding_vector), category_id=category_id)
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article

    @strawberry.mutation
    async def create_category(self, info, name: str) -> CategoryType:
        db: AsyncSession = info.context["db"]
        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @strawberry.mutation
    async def register_user(self, info, username: str, password: str) -> UserType:
        db: AsyncSession = info.context["db"]
        user = User(username=username, password_hash=await hash_password(password))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

async def get_context():
    async with get_db_session() as db:
        return {"db": db}

schema = strawberry.Schema(query=Query, mutation=Mutation)

# FastAPI App
app = FastAPI()
gql_router = GraphQLRouter(schema, context_getter=get_context)
app.include_router(gql_router, prefix="/graphql")

@app.post("/token")
async def login(form_data: dict):
    async with get_db_session() as db:
        result = await db.execute(select(User).filter(User.username == form_data["username"]))
        user = result.scalar_one_or_none()
        if not user or not await verify_password(form_data["password"], user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"access_token": await create_access_token({"sub": user.username}), "token_type": "bearer"}

@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "You have access", "user": user}

@app.get("/health")
async def health_check():
    return {"status": "OK"}
