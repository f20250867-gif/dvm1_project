from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    role  = forms.ChoiceField(choices=[
        (User.Role.PASSENGER, 'Passenger'),
        (User.Role.DRIVER,    'Driver'),
    ])

    class Meta:
        model  = User
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):                        # ← add this
        user      = super().save(commit=False)
        user.role = self.cleaned_data['role']           # ← explicitly set role
        if commit:
            user.save()
        return user