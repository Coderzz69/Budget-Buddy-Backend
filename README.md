# Budget Buddy Backend

A backend service for the Budget Buddy application, built with Node.js, Express, and Prisma. It provides a robust API for managing users, accounts, transactions, and more, utilizing Clerk for secure user authentication.

## Features

-   **User Authentication**: Seamlessly integrated with Clerk for secure user management.
-   **Account Management**: Create, read, update, and delete accounts (e.g., Bank, Cash).
-   **Transaction Management**: Record and categorize income and expenses.
-   **User Profile**: Manage user details and preferences (e.g., currency).
-   **Budgeting & Groups**: Comprehensive data model supporting budgets, group expenses, and settlements (via database schema).

## Tech Stack

-   **Runtime**: Node.js
-   **Framework**: Express.js
-   **Database**: PostgreSQL
-   **ORM**: Prisma
-   **Authentication**: Clerk
-   **Containerization**: Docker
-   **Deployment**: AWS ECS (Fargate)

## Prerequisites

-   Node.js (v18 or higher recommended)
-   npm (Node Package Manager)
-   PostgreSQL Database

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd budget-buddy-backend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root directory and add the following variables:

    ```env
    PORT=3000
    DATABASE_URL="postgresql://user:password@localhost:5432/budget_buddy?schema=public"
    CLERK_PUBLISHABLE_KEY=pk_test_...
    CLERK_SECRET_KEY=sk_test_...
    ```

    > **Note:** The `CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` are required for the Clerk SDK to function correctly. You can obtain these from your Clerk dashboard.

## Database Setup

1.  **Generate Prisma Client:**
    ```bash
    npx prisma generate
    ```

2.  **Run Migrations:**
    ```bash
    npx prisma migrate dev
    ```

    This will create the necessary tables in your PostgreSQL database based on the schema defined in `prisma/schema.prisma`.

## Running the Application

### Development Mode

To run the server with hot-reloading using `nodemon`:

```bash
npm run dev
```

### Production Mode

To run the server in production mode (runs migrations and starts the server):

```bash
npm start
```

## API Endpoints

### Authentication
-   `POST /auth/sync`: Syncs the authenticated Clerk user with the database.

### Accounts
-   `GET /accounts`: List all accounts for the authenticated user.
-   `POST /accounts`: Create a new account.
-   `PUT /accounts/:id`: Update an existing account.
-   `DELETE /accounts/:id`: Delete an account.

### Transactions
-   `GET /transactions`: List all transactions for the authenticated user.
-   `POST /transactions`: Create a new transaction.
-   `PUT /transactions/:id`: Update an existing transaction.
-   `DELETE /transactions/:id`: Delete a transaction.

### User Profile
-   `GET /user/profile`: Get the current user's profile.
-   `PUT /user/profile`: Update the current user's profile.
-   `GET /users`: List all users (restricted).

### Health Check
-   `GET /`: Welcome message.
-   `GET /health`: Health status.

## Deployment

The application is containerized using Docker. The `Dockerfile` is set up to install dependencies, generate the Prisma client, and start the application.

Configuration for AWS ECS Fargate is provided in `task-definition.json`.
