class AccessDenied(PermissionError):
    def __init__(self, should_raise=True, error_content="Access Denied."):
        self.should_raise = should_raise
        self.error_content = error_content
        super().__init__(self.error_content)
