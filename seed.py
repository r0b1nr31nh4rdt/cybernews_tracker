from database import init_db, create_user
init_db()
create_user("admin", "admin1234", role="admin")
create_user("analyst", "analyst1234", role="analyst")
print("Done.")
