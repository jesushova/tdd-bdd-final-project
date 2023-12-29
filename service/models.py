# Copyright 2016, 2023 John Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Models for Product Demo Service

All of the models are stored in this module

Models
------
Product - A Product used in the Product Store

Attributes:
-----------
name (string) - the name of the product
description (string) - the description of the product
available (boolean) - True for products that are available
price (decimal) - the price of the product
category (enum) - the category the product belongs to

"""
import logging
from enum import Enum
from decimal import Decimal
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal, InvalidOperation

logger = logging.getLogger("flask.app")

db = SQLAlchemy()

def init_db(app):
    Product.init_db(app)

class DataValidationError(Exception):
    pass

class Category(Enum):
    UNKNOWN = 0
    CLOTHS = 1
    FOOD = 2
    HOUSEWARES = 3
    AUTOMOTIVE = 4
    TOOLS = 5

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    available = db.Column(db.Boolean(), nullable=False, default=True)
    category = db.Column(db.Enum(Category), nullable=False, server_default=(Category.UNKNOWN.name))

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    def create(self):
        logger.info("Creating %s", self.name)
        self.id = None
        db.session.add(self)
        db.session.commit()

    def update(self):
        logger.info("Saving %s", self.name)
        if not self.id or not self.query.get(self.id):
            logger.error("Attempt to update a Product with invalid ID")
            raise DataValidationError("Update called with invalid ID field")
        db.session.commit()

    def delete(self):
        """Removes a Product from the data store"""
        logger.info("Deleting %s", self.name)
        if not self.id:
            logger.error("Attempt to delete a Product with no id")
            raise DataValidationError("Delete called with empty ID field")
        product = Product.query.get(self.id)
        if not product:
            logger.error("Attempt to delete a Product that does not exist")
            raise DataValidationError("Attempt to delete a Product that does not exist")
        db.session.delete(product)
        db.session.commit()

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "available": self.available,
            "category": self.category.name
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Product from a dictionary
        """
        if not isinstance(data, dict):
            raise DataValidationError("Invalid data format for deserializing a Product")

        try:
            self.name = data["name"]
            self.description = data["description"]
            try:
                self.price = Decimal(data["price"])
            except InvalidOperation:
                raise DataValidationError("Invalid price value")

            self.available = data["available"]
            self.category = getattr(Category, data["category"])
        except KeyError as error:
            raise DataValidationError(f"Invalid product: missing {error.args[0]}")
        except (TypeError, ValueError) as error:
            raise DataValidationError(f"Invalid value for product: {error}")

        if not self.name or not self.description:
            raise DataValidationError("Invalid product: name and description are required")
        if self.price < 0:
            raise DataValidationError("Invalid product: price must be >= 0")

        return self

    @classmethod
    def init_db(cls, app: Flask):
        logger.info("Initializing database")
        db.init_app(app)
        app.app_context().push()
        db.create_all()

    @classmethod
    def all(cls) -> list:
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, product_id: int):
        logger.info("Processing lookup for id %s ...", product_id)
        return cls.query.get(product_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_price(cls, price: Decimal) -> list:
        logger.info("Processing price query for %s ...", price)
        return cls.query.filter(cls.price == price)

    @classmethod
    def find_by_availability(cls, available: bool = True) -> list:
        logger.info("Processing available query for %s ...", available)
        return cls.query.filter(cls.available == available)

    @classmethod
    def find_by_category(cls, category: Category) -> list:
        """Returns all Products by their Category"""
        logger.info("Processing category query for %s ...", category.name)
        return cls.query.filter(cls.category == category).all()

    @staticmethod
    def test_deserialize_with_missing_data():
        """It should not deserialize a Product with missing data"""
        test_product = ProductFactory()
        data = test_product.serialize()
        del data["name"]  # remove name to simulate missing data
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    @staticmethod
    def test_deserialize_with_bad_data():
        """It should not deserialize a Product with bad data"""
        test_product = ProductFactory()
        data = test_product.serialize()
        data["price"] = "not-a-decimal"  # invalid price
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    @staticmethod
    def test_find_by_category():
        """It should find Products by their Category"""
        Product(name="Test1", category=Category.FOOD).create()
        Product(name="Test2", category=Category.TOOLS).create()
        found = Product.find_by_category(Category.FOOD)
        assert all(product.category == Category.FOOD for product in found)

    # Test deserialization with missing fields
    def test_deserialize_with_missing_data(self):
        """It should not deserialize a Product with missing data"""
        test_product = ProductFactory()
        data = test_product.serialize()
        del data["name"]  # remove name to simulate missing data
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    # Test deserialization with invalid data types
    def test_deserialize_with_bad_data(self):
        """It should not deserialize a Product with bad data"""
        test_product = ProductFactory()
        data = test_product.serialize()
        data["price"] = "not-a-decimal"  # invalid price
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    