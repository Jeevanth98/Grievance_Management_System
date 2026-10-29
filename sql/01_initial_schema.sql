-- =====================================================================
-- 01_INITIAL_SCHEMA.SQL: CORE STUDENT & GRIEVANCE MANAGEMENT SCHEMA
-- =====================================================================

-- 1. Create Enums
DO $$ BEGIN
    CREATE TYPE grievance_status AS ENUM (
        'submitted',
        'under_review',
        'assigned',
        'in_progress',
        'resolved',
        'closed',
        'rejected',
        'reopened'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE grievance_priority AS ENUM (
        'low',
        'medium',
        'high',
        'urgent'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Grievance Categories
CREATE TABLE IF NOT EXISTS public.grievance_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Students Profile Table (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    register_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    phone_number TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Core Grievances Table
CREATE TABLE IF NOT EXISTS public.grievances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number TEXT UNIQUE NOT NULL,
    student_auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES public.grievance_categories(id),
    title TEXT NOT NULL CHECK (char_length(trim(title)) > 0),
    description TEXT NOT NULL CHECK (char_length(trim(description)) > 0),
    status grievance_status DEFAULT 'submitted' NOT NULL,
    priority grievance_priority DEFAULT 'medium' NOT NULL,
    is_anonymous BOOLEAN DEFAULT false NOT NULL,
    assigned_admin_id UUID, -- References public.admin_profiles(id) defined in 02_admin_extensions
    admin_updated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    reopened_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Indexing for high-performance querying & filtering
CREATE INDEX IF NOT EXISTS idx_grievances_student_auth ON public.grievances(student_auth_user_id);
CREATE INDEX IF NOT EXISTS idx_grievances_status ON public.grievances(status);
CREATE INDEX IF NOT EXISTS idx_grievances_priority ON public.grievances(priority);
CREATE INDEX IF NOT EXISTS idx_grievances_category ON public.grievances(category_id);
CREATE INDEX IF NOT EXISTS idx_grievances_assigned_admin ON public.grievances(assigned_admin_id);
CREATE INDEX IF NOT EXISTS idx_grievances_created_at ON public.grievances(created_at DESC);

-- 5. Status History Table
CREATE TABLE IF NOT EXISTS public.grievance_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES public.grievances(id) ON DELETE CASCADE,
    old_status grievance_status,
    new_status grievance_status NOT NULL,
    changed_by_user_id UUID NOT NULL, -- references auth.users(id)
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_status_history_grievance ON public.grievance_status_history(grievance_id);

-- 6. Official Comments Table
CREATE TABLE IF NOT EXISTS public.grievance_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES public.grievances(id) ON DELETE CASCADE,
    author_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    author_role TEXT NOT NULL CHECK (author_role IN ('student', 'admin')),
    comment TEXT NOT NULL CHECK (char_length(trim(comment)) > 0 AND char_length(comment) <= 4000),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comments_grievance ON public.grievance_comments(grievance_id);

-- 7. Attachments Table
CREATE TABLE IF NOT EXISTS public.grievance_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES public.grievances(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_type TEXT,
    file_size BIGINT CHECK (file_size > 0),
    uploaded_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attachments_grievance ON public.grievance_attachments(grievance_id);

-- 8. Notifications Table
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    grievance_id UUID NOT NULL REFERENCES public.grievances(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notifications_student ON public.notifications(student_auth_user_id, is_read);
