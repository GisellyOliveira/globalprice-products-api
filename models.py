from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    """
    Product Model
    Represents the 'products' table on database.
    """
    __tablename__ = 'products'

    # Columns definition
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(225), nullable=True)
    base_price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """
        Helper method to convert the object to a Dictionary (JSON ready).
        """
        return{
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "base_price": self.base_price
        }
    