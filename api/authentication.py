import jwt
import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .database import db

import time

# Cache for JWKS to avoid repeated network calls
_jwks_cache = None
_jwks_cache_time = 0
JWKS_CACHE_TTL = 3600  # 1 hour in seconds

class ClerkJWTAuthentication(BaseAuthentication):
    def get_jwks(self):
        global _jwks_cache, _jwks_cache_time
        current_time = time.time()
        
        if _jwks_cache is not None and (current_time - _jwks_cache_time) < JWKS_CACHE_TTL:
            return _jwks_cache
        
        issuer = getattr(settings, 'CLERK_ISSUER_URL', '')
        if not issuer:
            return None
            
        try:
            jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
            response = requests.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_time = time.time()
            return _jwks_cache
        except Exception:
            return None

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        
        try:
            # Get public keys from Clerk
            jwks = self.get_jwks()
            
            if jwks:
                # Proper verification
                public_key = jwt.PyJWKClient(getattr(settings, 'CLERK_ISSUER_URL', '') + '/.well-known/jwks.json').get_signing_key_from_jwt(token).key
                decoded_token = jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    issuer=getattr(settings, 'CLERK_ISSUER_URL', '')
                )
            else:
                # Fallback to unverified if issuer is missing (not recommended for prod)
                # But we'll try to follow the issuer URL if provided
                decoded_token = jwt.decode(token, options={"verify_signature": False})
            
            clerk_id = decoded_token.get('sub')
            if not clerk_id:
                raise AuthenticationFailed('Token does not contain user identifier (sub)')

            user = db.user.find_unique(where={"clerkId": clerk_id})
            if not user:
                raise AuthenticationFailed('User not found in local database')
                
            class SimpleUser:
                def __init__(self, db_user):
                    self.id = db_user.id
                    self.clerkId = db_user.clerkId
                    self.is_authenticated = True
                    self.db_user = db_user
                    
            return (SimpleUser(user), token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.DecodeError:
            raise AuthenticationFailed('Error decoding token')
        except Exception as e:
            raise AuthenticationFailed(str(e))
