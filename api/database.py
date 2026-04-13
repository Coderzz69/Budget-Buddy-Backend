from prisma import Prisma
import atexit

db = Prisma(auto_register=True)
db.connect()

@atexit.register
def shutdown():
    if db.is_connected():
        db.disconnect()
