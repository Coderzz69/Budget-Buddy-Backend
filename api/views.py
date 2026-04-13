import uuid
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserSerializer, AccountSerializer, CategorySerializer,
    TransactionSerializer, BudgetSerializer
)
from .database import db
from datetime import datetime, timedelta

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.user.id
        # Calculate total balance across all accounts
        accounts = db.account.find_many(where={"userId": user_id})
        total_balance = sum(account.balance for account in accounts)
        
        # Calculate monthly spend
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        transactions = db.transaction.find_many(
            where={
                "userId": user_id, 
                "type": "expense",
                "occurredAt": {"gte": start_of_month}
            }
        )
        monthly_spend = sum(tx.amount for tx in transactions)
        
        # Calculate budget usage
        budgets = db.budget.find_many(
            where={
                "userId": user_id,
                "month": {"gte": start_of_month}
            }
        )
        total_budget_limit = sum(b.limit for b in budgets)
        
        return Response({
            "totalBalance": total_balance,
            "monthlySpend": monthly_spend,
            "budgetLimit": total_budget_limit
        })

class SyncUserView(APIView):
    authentication_classes = [] 
    permission_classes = []

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            user = db.user.upsert(
                where={"clerkId": data["clerkId"]},
                data={
                    "create": {
                        "clerkId": data["clerkId"],
                        "email": data["email"],
                        "name": data.get("name"),
                        "phoneNumber": data.get("phoneNumber"),
                        "profilePic": data.get("profilePic"),
                        "currency": data.get("currency", "INR"),
                    },
                    "update": {
                        "email": data["email"],
                        "name": data.get("name"),
                        "phoneNumber": data.get("phoneNumber"),
                        "profilePic": data.get("profilePic"),
                        "currency": data.get("currency", "INR"),
                    }
                }
            )
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        accounts = db.account.find_many(where={"userId": request.user.id})
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        account = db.account.find_first(where={"id": pk, "userId": request.user.id})
        if not account:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(AccountSerializer(account).data)

    def create(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            account = db.account.create({
                "userId": request.user.id,
                "name": data["name"],
                "type": data["type"],
                "balance": data["balance"],
            })
            return Response(AccountSerializer(account).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        account = db.account.find_first(where={"id": pk, "userId": request.user.id})
        if not account:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            updated_account = db.account.update(
                where={"id": pk},
                data={
                    "name": data["name"],
                    "type": data["type"],
                    "balance": data["balance"],
                }
            )
            return Response(AccountSerializer(updated_account).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        account = db.account.find_first(where={"id": pk, "userId": request.user.id})
        if not account:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # Prisma will handle cascade deletes if set up, or we might need to delete tx first
        try:
            db.account.delete(where={"id": pk})
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        categories = db.category.find_many(where={
            "OR": [
                {"userId": request.user.id},
                {"userId": None}
            ]
        })
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        category = db.category.find_first(where={
            "id": pk, 
            "OR": [{"userId": request.user.id}, {"userId": None}]
        })
        if not category:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data)

    def create(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                category = db.category.create({
                    "userId": request.user.id,
                    "name": data["name"],
                    "icon": data.get("icon"),
                    "color": data.get("color"),
                })
                return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        category = db.category.find_first(where={"id": pk, "userId": request.user.id})
        if not category:
            return Response({"error": "Category not found or read-only"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            updated_category = db.category.update(
                where={"id": pk},
                data={
                    "name": data["name"],
                    "icon": data.get("icon"),
                    "color": data.get("color"),
                }
            )
            return Response(CategorySerializer(updated_category).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        category = db.category.find_first(where={"id": pk, "userId": request.user.id})
        if not category:
            return Response({"error": "Category not found or read-only"}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            db.category.delete(where={"id": pk})
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TransactionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        account_id = request.query_params.get("account_id")
        category_id = request.query_params.get("category_id")

        filters = {"userId": request.user.id}
        if account_id:
            filters["accountId"] = account_id
        if category_id:
            filters["categoryId"] = category_id
        
        if start_date or end_date:
            occurred_at_filter = {}
            if start_date:
                occurred_at_filter["gte"] = start_date 
            if end_date:
                occurred_at_filter["lte"] = end_date
            filters["occurredAt"] = occurred_at_filter

        page = int(request.query_params.get("page", 1))
        page_size = 20
        skip = (page - 1) * page_size

        transactions = db.transaction.find_many(
            where=filters,
            order={"occurredAt": "desc"},
            skip=skip,
            take=page_size
        )
        total = db.transaction.count(where=filters)
        
        return Response({
            "count": total,
            "page": page,
            "results": TransactionSerializer(transactions, many=True).data
        })

    def retrieve(self, request, pk=None):
        transaction = db.transaction.find_first(where={"id": pk, "userId": request.user.id})
        if not transaction:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(TransactionSerializer(transaction).data)

    def create(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            if data["amount"] <= 0:
                return Response({"error": "Amount must be strictly positive."}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                # Use sync interactive transaction
                with db.tx() as transaction_db:
                    account = transaction_db.account.find_unique(where={"id": data["accountId"]})
                    if not account or account.userId != request.user.id:
                        raise Exception("Account not found or not owned by user.")
                    
                    new_balance = account.balance
                    amount = data["amount"]
                    if data["type"] == "expense":
                        new_balance -= amount
                    elif data["type"] == "income":
                        new_balance += amount
                        
                    transaction_db.account.update(
                        where={"id": account.id},
                        data={"balance": new_balance}
                    )
                    
                    new_tx = transaction_db.transaction.create({
                        "userId": request.user.id,
                        "accountId": account.id,
                        "categoryId": data.get("categoryId"),
                        "type": data["type"],
                        "amount": amount,
                        "note": data.get("note"),
                        "occurredAt": data["occurredAt"]
                    })
                
                return Response(TransactionSerializer(new_tx).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        transaction = db.transaction.find_first(where={"id": pk, "userId": request.user.id})
        if not transaction:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        try:
            with db.tx() as transaction_db:
                account = transaction_db.account.find_unique(where={"id": transaction.accountId})
                if account:
                    # Rollback the transaction amount
                    new_balance = account.balance
                    if transaction.type == "expense":
                        new_balance += transaction.amount
                    elif transaction.type == "income":
                        new_balance -= transaction.amount
                        
                    transaction_db.account.update(
                        where={"id": account.id},
                        data={"balance": new_balance}
                    )
                
                transaction_db.transaction.delete(where={"id": pk})
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BudgetViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        budgets = db.budget.find_many(where={"userId": request.user.id})
        return Response(BudgetSerializer(budgets, many=True).data)

    def retrieve(self, request, pk=None):
        budget = db.budget.find_first(where={"id": pk, "userId": request.user.id})
        if not budget:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(BudgetSerializer(budget).data)

    def create(self, request):
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                budget = db.budget.create({
                    "userId": request.user.id,
                    "categoryId": data["categoryId"],
                    "month": data["month"],
                    "limit": data["limit"]
                })
                return Response(BudgetSerializer(budget).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, pk=None):
        budget = db.budget.find_first(where={"id": pk, "userId": request.user.id})
        if not budget:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            updated_budget = db.budget.update(
                where={"id": pk},
                data={
                    "categoryId": data["categoryId"],
                    "month": data["month"],
                    "limit": data["limit"]
                }
            )
            return Response(BudgetSerializer(updated_budget).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        budget = db.budget.find_first(where={"id": pk, "userId": request.user.id})
        if not budget:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        try:
            db.budget.delete(where={"id": pk})
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
