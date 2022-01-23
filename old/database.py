from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#### Database Classes ####

class LocationTable(db.Model):

    __tablename__ = "location_table"
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Primary key: {self.id} ---- Location: {self.location}"

class DegreeDataTable(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location_table.id"), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, unique=False)
    temp_c = db.Column(db.Float, nullable=False, unique=False)
    CDD_10_5 = db.Column(db.Float, nullable=False, unique=False)
    CDD_15_5 = db.Column(db.Float, nullable=False, unique=False)
    CDD_18_5 = db.Column(db.Float, nullable=False, unique=False)
    HDD_10_5 = db.Column(db.Float, nullable=False, unique=False)
    HDD_15_5 = db.Column(db.Float, nullable=False, unique=False)
    HDD_18_5 = db.Column(db.Float, nullable=False, unique=False)

    def __repr__(self) -> str:
        return f"Degree key: {self.degree_key} /n base_temperature: {self.temp_c}"

class UserTable(db.Model):

    user_id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    e_mail = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean, unique=False)

    def __repr__(self) -> str:
        return f"e_mail: {self.e_mail} /n admin: {self.admin}"

if __name__ == "__main__":
    #db.create_all()
    print("Database created!")