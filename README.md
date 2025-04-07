# GraphQL-powered FastAPI Knowledge Base

A robust FastAPI application implementing a knowledge base system with GraphQL API, PostgreSQL database, and semantic search capabilities.

## Features

- GraphQL API using Strawberry
- JWT Authentication
- PostgreSQL with async support
- Semantic search using sentence transformers
- Role-based access control
- Article categorization system

## Tech Stack

- FastAPI
- PostgreSQL + AsyncPG
- Strawberry GraphQL
- SentenceTransformer
- SQLAlchemy (Async)
- JWT + bcrypt

## API Endpoints

- `/graphql` - GraphQL endpoint
- `/token` - JWT token authentication
- `/protected` - Protected route example
- `/health` - Health check endpoint

## GraphQL Operations

### Queries
- `listArticles` - Get all articles
- `getArticle` - Get article by ID
- `listCategories` - Get all categories
- `protectedInfo` - Get protected user information

### Mutations
- `createArticle` - Create new article with semantic embedding
- `createCategory` - Create new category
- `registerUser` - Register new user

## Database Models

- User (Authentication and authorization)
- Category (Article organization)
- Article (Content with semantic embeddings)

## Setup

1. Configure PostgreSQL database
2. Set environment variables:
   - DATABASE_URL
   - SECRET_KEY
3. Install dependencies
4. Run migrations
5. Start the server

## Security

- Password hashing using bcrypt
- JWT token authentication
- Protected routes and operations