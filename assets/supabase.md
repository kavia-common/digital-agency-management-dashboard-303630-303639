# Supabase Configuration for Project Management Backend

## Overview
This document describes the Supabase configuration required for the Digital Agency Project Management backend API.

## Database Schema

### Tables Required

#### 1. user_profiles
Stores extended user profile information beyond what Supabase Auth provides.

```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Row Level Security (RLS):**
- Enable RLS on this table
- Users can only read and update their own profile
- Policy: `(auth.uid() = id)`

#### 2. projects
Stores project information for each user.

```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'active',
  budget NUMERIC(12, 2),
  start_date TIMESTAMPTZ,
  end_date TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Row Level Security (RLS):**
- Enable RLS on this table
- Users can only access their own projects
- Policy: `(auth.uid() = user_id)`

#### 3. clients
Stores client information for each user.

```sql
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  company TEXT,
  address TEXT,
  notes TEXT,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Row Level Security (RLS):**
- Enable RLS on this table
- Users can only access their own clients
- Policy: `(auth.uid() = user_id)`

#### 4. user_settings
Stores user preferences and settings.

```sql
CREATE TABLE user_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  theme TEXT DEFAULT 'light',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Row Level Security (RLS):**
- Enable RLS on this table
- Users can only access their own settings
- Policy: `(auth.uid() = user_id)`

## Authentication Configuration

### Email Templates
Configure email templates in Supabase Dashboard under Authentication > Email Templates:

1. **Confirmation Email**: Sent when users sign up
2. **Password Reset**: Sent when users request password reset
3. **Email Change**: Sent when users change their email

### Redirect URLs
Add the following redirect URLs in Supabase Dashboard under Authentication > URL Configuration:

- `https://vscode-internal-31918-beta.beta01.cloud.kavia.ai:3000/auth/callback`
- `https://vscode-internal-31918-beta.beta01.cloud.kavia.ai:3000/reset-password`
- `http://localhost:3000/auth/callback` (for local development)
- `http://localhost:3000/reset-password` (for local development)

## Database Functions (Optional)

### Auto-update timestamps
Create a function to automatically update the `updated_at` timestamp:

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
  BEFORE UPDATE ON clients
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at
  BEFORE UPDATE ON user_settings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Environment Variables

The following environment variables are required in the `.env` file:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key
- `JWT_SECRET`: Secret key for JWT token signing (optional, uses Supabase tokens by default)

## Security Considerations

1. **Row Level Security**: All tables must have RLS enabled to prevent unauthorized access
2. **API Keys**: Never expose the service_role key in client-side code
3. **CORS**: Configure allowed origins in the backend to prevent unauthorized access
4. **Email Verification**: Consider enabling email verification for new signups

## Integration Notes

- The backend uses the Supabase Python client (`supabase-py`)
- Authentication is handled through Supabase Auth
- JWT tokens from Supabase are used for API authentication
- All database operations respect RLS policies
