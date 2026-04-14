from sqlalchemy.orm import Session
from . import models, database, auth

def seed_db():
    db = database.SessionLocal()
    
    print("Dropping all tables to ensure clean slate...")
    models.Base.metadata.drop_all(bind=database.engine)
    models.Base.metadata.create_all(bind=database.engine)
    
    print("Seeding database...")

    # Tenants
    tenant_a = models.Tenant(name="Tenant A")
    tenant_b = models.Tenant(name="Tenant B")
    db.add(tenant_a)
    db.add(tenant_b)
    db.commit()

    # Users
    # Admin
    admin = models.User(
        username="admin", 
        hashed_password=auth.get_password_hash("admin123"),
        role="admin",
        tenant_id=tenant_a.id,
        api_key="sk_live_ADMIN_SECRET_KEY"
    )
    
    # User A
    user_a = models.User(
        username="user_a", 
        hashed_password=auth.get_password_hash("password_a"),
        role="user",
        tenant_id=tenant_a.id,
        api_key="sk_live_USER_A_KEY"
    )
    
    # User B
    user_b = models.User(
        username="user_b", 
        hashed_password=auth.get_password_hash("password_b"),
        role="user",
        tenant_id=tenant_b.id,
        api_key="sk_live_USER_B_KEY"
    )

    db.add(admin)
    db.add(user_a)
    db.add(user_b)
    db.commit()

    # Invoices
    inv1 = models.Invoice(amount=100.0, status="paid", tenant_id=tenant_a.id)
    inv2 = models.Invoice(amount=5000.0, status="pending", tenant_id=tenant_b.id) # Target for IDOR
    db.add(inv1)
    db.add(inv2)

    # Notes
    note1 = models.Note(title="Welcome", content="Welcome to Tenant A", user_id=user_a.id, tenant_id=tenant_a.id)
    db.add(note1)
    
    db.commit()
    db.close()
    print("Database seeded.")

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=database.engine)
    seed_db()
