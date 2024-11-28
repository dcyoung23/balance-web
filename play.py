import os
from sqlalchemy import create_engine, inspect
from sql import SQL

#engine = create_engine("postgresql://balance_user:balance@localhost/balance")
#print(inspect(engine).get_table_names())

db = SQL("postgresql://balance_user:balance@localhost/balance")

print(os.getenv('DATABASE_URL'))