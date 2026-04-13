from rest_framework import serializers

class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    clerkId = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField(required=False, allow_null=True)
    phoneNumber = serializers.CharField(required=False, allow_null=True)
    profilePic = serializers.CharField(required=False, allow_null=True)
    currency = serializers.CharField(default="INR")
    createdAt = serializers.DateTimeField(read_only=True)
    updatedAt = serializers.DateTimeField(read_only=True)

class AccountSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    userId = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    type = serializers.ChoiceField(choices=["cash", "bank", "card", "wallet"])
    balance = serializers.FloatField(default=0.0)
    createdAt = serializers.DateTimeField(read_only=True)

class CategorySerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    userId = serializers.CharField(read_only=True, allow_null=True)
    name = serializers.CharField(max_length=255)
    icon = serializers.CharField(required=False, allow_null=True)
    color = serializers.CharField(required=False, allow_null=True)
    createdAt = serializers.DateTimeField(read_only=True)

class TransactionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    userId = serializers.CharField(read_only=True)
    accountId = serializers.CharField()
    categoryId = serializers.CharField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=["income", "expense"])
    amount = serializers.FloatField()
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    occurredAt = serializers.DateTimeField()
    createdAt = serializers.DateTimeField(read_only=True)

class BudgetSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    userId = serializers.CharField(read_only=True)
    categoryId = serializers.CharField()
    month = serializers.DateTimeField()
    limit = serializers.FloatField()
    createdAt = serializers.DateTimeField(read_only=True)
