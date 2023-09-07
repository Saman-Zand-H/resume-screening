from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model


class AuthTestCase(GraphQLTestCase):
    GRAPHQL_URL = "/graphql"

    def setUp(self):
        self.register_user_mutation = """
        mutation RegisterUser($email: String!, $firstName: String!, $lastName: String!) {
            register(
                email: $email,
                firstName: $firstName,
                lastName: $lastName,
            ) {
                success,
                errors
            }
        }
        """

        self.obtain_jwt_token_mutation = """
        mutation ObtainJWTToken($email: String!, $password: String!) {
            tokenAuth(
                email: $email,
                password: $password
            ) {
                success,
                errors,
                token,
                refreshToken,
                unarchiving,
                user {
                  email
                }
            }
        }
        """

    def register_user(self, variables):
        response = self.query(self.register_user_mutation, operation_name="RegisterUser", variables=variables)
        return response.json()

    def obtain_jwt_token(self, variables):
        response = self.query(self.obtain_jwt_token_mutation, operation_name="ObtainJWTToken", variables=variables)
        return response.json()

    def test_register(self):
        variables = {
            "email": "testuser@example.com",
            "firstName": "Test",
            "lastName": "User",
        }

        response = self.register_user(variables)

        self.assertTrue(response["data"]["register"]["success"])
        self.assertIsNone(response["data"]["register"]["errors"])

        user = get_user_model().objects.get(email=variables["email"])
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, variables["firstName"])
        self.assertEqual(user.last_name, variables["lastName"])
        self.assertFalse(user.status.verified)

    def test_register_with_existing_email(self):
        get_user_model().objects.create_user(
            email="existing@example.com", username="existing", first_name="Existing", last_name="User"
        )

        variables = {
            "email": "existing@example.com",
            "firstName": "Test",
            "lastName": "User",
        }

        response = self.register_user(variables)

        self.assertFalse(response["data"]["register"]["success"])
        self.assertIsNotNone(response["data"]["register"]["errors"]["email"])
        self.assertEqual(
            response["data"]["register"]["errors"]["email"], ["User with this Email address already exists."]
        )

    def test_register_without_name_fields(self):
        variables = {
            "email": "testuser@example.com",
        }

        response = self.register_user(variables)

        self.assertEqual(len(response["errors"]), 2)
        self.assertEqual(
            response["errors"][0]["message"], "Variable '$firstName' of required type 'String!' was not provided."
        )
        self.assertEqual(
            response["errors"][1]["message"], "Variable '$lastName' of required type 'String!' was not provided."
        )

    def test_register_with_invalid_email(self):
        variables = {
            "email": "invalid-email",
            "firstName": "Test",
            "lastName": "User",
        }

        response = self.register_user(variables)

        self.assertFalse(response["data"]["register"]["success"])
        self.assertIsNotNone(response["data"]["register"]["errors"]["email"])
        self.assertEqual(response["data"]["register"]["errors"]["email"], ["Enter a valid email address."])

    def test_token_auth_unverified_account(self):
        variables = {
            "email": "testuser@example.com",
            "password": "password",
        }

        get_user_model().objects.create_user(
            email=variables["email"],
            username="testuser",
            first_name="Test",
            last_name="User",
            password=variables["password"],
        )

        response = self.obtain_jwt_token(variables)

        self.assertFalse(response["data"]["tokenAuth"]["success"])
        self.assertEqual(response["data"]["tokenAuth"]["errors"]["message"], "Please verify your account.")
        self.assertIsNone(response["data"]["tokenAuth"]["token"])
        self.assertIsNone(response["data"]["tokenAuth"]["refreshToken"])
        self.assertIsNone(response["data"]["tokenAuth"]["user"])

    def test_token_auth_verified_account(self):
        variables = {
            "email": "testuser@example.com",
            "password": "password",
        }

        user = get_user_model().objects.create_user(
            email=variables["email"],
            username="testuser",
            first_name="Test",
            last_name="User",
            password=variables["password"],
        )
        user.status.verified = True
        user.status.save()

        response = self.obtain_jwt_token(variables)

        self.assertTrue(response["data"]["tokenAuth"]["success"])
        self.assertIsNone(response["data"]["tokenAuth"]["errors"])
        self.assertIsNotNone(response["data"]["tokenAuth"]["token"])
        self.assertIsNotNone(response["data"]["tokenAuth"]["refreshToken"])
        self.assertIsNotNone(response["data"]["tokenAuth"]["user"])
        self.assertEqual(response["data"]["tokenAuth"]["user"]["email"], variables["email"])

    def test_token_auth_with_invalid_credentials(self):
        variables = {
            "email": "testuser@gmail.com",
            "password": "wrong_password",
        }

        user = get_user_model().objects.create_user(
            email=variables["email"],
            username="testuser",
            first_name="Test",
            last_name="User",
            password="password",
        )
        user.status.verified = True
        user.status.save()

        response = self.obtain_jwt_token(variables)

        self.assertFalse(response["data"]["tokenAuth"]["success"])
        self.assertEqual(response["data"]["tokenAuth"]["errors"]["message"], "Please, enter valid credentials.")
        self.assertIsNone(response["data"]["tokenAuth"]["token"])
        self.assertIsNone(response["data"]["tokenAuth"]["refreshToken"])
        self.assertIsNone(response["data"]["tokenAuth"]["user"])
