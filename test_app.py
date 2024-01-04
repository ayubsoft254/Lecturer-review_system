import unittest
from flask import Flask, session
from flask_testing import TestCase
from app import app, db, User, Feedback
from bs4 import BeautifulSoup

class TestApp(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_user_registration(self):
        response = self.client.post(
            url_for('signup'),
            data={'username': 'testuser', 'password': 'testpassword', 'email': 'test@example.com', 'student_name': 'Test User', 'student_id': '1234'},
            follow_redirects=True
        )
        self.assert200(response)
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertIn('Signup successful!', str(soup))

    def test_user_login(self):
        response = self.client.post(
            url_for('login'),
            data={'username': 'testuser', 'password': 'testpassword'},
            follow_redirects=True
        )
        self.assert200(response)
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertIn('Login successful!', str(soup))

    def test_feedback_submission(self):
        # Assuming you have a logged-in user before submitting feedback
        # This might involve a login request using self.client.post(url_for('login'), data={'username': 'testuser', 'password': 'testpassword'})
        
        response = self.client.post(
            url_for('submit'),
            data={'lecturer': 'Test Lecturer', 'rating': '5', 'comments': 'Great lecturer!'},
            follow_redirects=True
        )
        self.assert200(response)
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertIn('Feedback submitted successfully!', str(soup))

if __name__ == '__main__':
    unittest.main()