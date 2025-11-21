# User App

`user` holds the custom Django `User` model and accompanying signals, forms, serializers, and views
for managing accounts inside Campfire Connections.

## Responsibilities

- Custom `User` model (`user/models.py`) with `UserType` enum, admin flags, and signal hooks for
  creating leader/attendee/faculty profiles automatically.
- Base profile classes (`BaseUserProfile`) shared by the faction/facility apps.
- Forms for registration and profile updates (`user/forms.py`).
- Serializers for summarizing users and profile data in APIs (`user/serializers.py`).
- Account views (login/logout/dashboard) and templates under `user/templates`.

## Key Points

- Signals in `user/models.py` automatically create and sync the appropriate profile whenever a
  user is created or their name changes.
- `ProfileUserFieldsMixin` consolidates first/last/email/phone fields across profile forms.
- The dashboard view defers to the portal registry, so user dashboards automatically pick up the
  correct template and widgets based on role.

## Tests

```bash
python manage.py test user
```

Use these tests to validate signal behavior and any new forms or serializers added to the user app.
