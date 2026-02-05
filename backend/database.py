from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# =========================
# Database Configuration
# =========================

DATABASE_URL = "sqlite:///./invoices.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =========================
# Invoice (Header Table)
# =========================

class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(String, primary_key=True, index=True)
    invoice_date = Column(Date, nullable=False)

    # Seller Details
    seller_name = Column(String, nullable=False)
    seller_state = Column(String)
    seller_gstin = Column(String)

    # Buyer Details
    buyer_name = Column(String, nullable=False)
    buyer_state = Column(String)
    buyer_gstin = Column(String)

    # Amount Summary
    sub_total = Column(Float, nullable=False)
    cgst_total = Column(Float, default=0.0)
    sgst_total = Column(Float, default=0.0)
    igst_total = Column(Float, default=0.0)
    total_tax = Column(Float, nullable=False)
    grand_total = Column(Float, nullable=False)

    # Extra Info
    payment_method = Column(String)
    terms_conditions = Column(Text)

    # Relationship
    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )


# =========================
# Invoice Items (Line Items)
# =========================

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, ForeignKey("invoices.invoice_id"), nullable=False)

    description = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    hsn_code = Column(String)
    item_category = Column(String)

    cgst_rate = Column(Float, default=0.0)
    sgst_rate = Column(Float, default=0.0)
    igst_rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="items")


# =========================
# DB Utilities
# =========================

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
