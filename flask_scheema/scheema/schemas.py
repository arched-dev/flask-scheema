class DeleteSuccessfulSchema(Schema):
    class Meta:
        name = "delete-success"

    # Successful Delete
    message = fields.Str(required=True)


class LoginInputSchema(Schema):
    """
    Schema for the login route, this is used to validate the data sent to the route.
    """

    class Meta:
        dump = False
        name = "login"

    email = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Users email address",
            "type": "string",
            "format": "email",
        },
    )
    password = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Users password",
            "type": "string",
            "format": "password",
        },
    )


class ResetPasswordSchemaIn(Schema):
    class Meta:
        name = "reset-password"

    email = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Users email address",
            "type": "string",
            "format": "email",
        },
    )


class ResetPasswordSchemaOut(Schema):
    class Meta:
        name = "reset-password-success"

    message = fields.Str(
        dump_only=True,
        metadata={
            "description": "Repsonse message",
            "type": "string",
            "format": "email",
        },
    )


class UserSchema(AutoScheema):
    class Meta:
        name = "user"
        model = User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @pre_load
    def remove_unwanted_fields(self, data, **kwargs):
        if "password_hash" in data:
            data.pop("password_hash", None)
        if "roles" in data:
            data.pop("roles", None)
        if "password" in data:
            self.password = data.pop("password", None)

        return data

    password = fields.Str(required=False)

    @post_load
    def make_instance(self, data, **kwargs):
        """
        Creates an instance of the model from the data, and sets the password if it exists (there is an issue with
        setter methods and SQLAlchemyAutoScheema, so this is a workaround)
        Args:
            data (dict): The data to be loaded
            **kwargs (dict): The keyword arguments

        Returns:

        """
        instance = self.Meta.model(**data)

        for key, value in data.items():
            setattr(instance, key, value)

        if hasattr(self, "password"):
            instance.password = self.password

        return instance

    @validates("email")
    def validate_email(self, value):
        """
        Validate email using email_validator library.
        """
        try:
            # Validate.
            validate_email(value)
        except EmailNotValidError as e:
            raise ValidationError(str(e))

    @validates("password")
    def validate_password(self, value):
        """
        Validate password based on custom logic.
        For example, let's enforce a minimum length of 8 characters.
        """
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

    @post_dump
    def add_roles(self, data, **kwargs):
        """
        Adds the roles to the user object
        Args:
            data (dict): The data to be dumped
            **kwargs (dict): The keyword arguments

        Returns:
            dict: The data with the roles added
        """
        user = db.session.query(User).get(data["id"])
        data["roles"] = [role.role_name for role in user.roles]
        return data


class TokenRefreshSchema(Schema):
    class Meta:
        name = "token-refresh"

    access_token = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            "description": "Access token",
            "type": "string",
            "format": "password",
        },
    )

    refresh_token = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            "description": "Refresh token",
            "type": "string",
            "format": "password",
        },
    )
    user = fields.Nested(UserSchema, dump_only=True)


class RefreshInputSchema(Schema):
    class Meta:
        dump = False
        name = "refresh-token"

    refresh_token = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Refresh token",
            "type": "string",
            "format": "password",
        },
    )


class RefreshOutputSchema(Schema):
    class Meta:
        name = "refresh-token-success"

    access_token = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            "description": "Access token",
            "type": "string",
            "format": "password",
        },
    )
