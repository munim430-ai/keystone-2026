-- =========================================================
-- KEYSTONE B2B & STUDENT CRM - SUPABASE DATABASE SCHEMA
-- Paste this script into your Supabase SQL Editor and click RUN
-- =========================================================

-- 1. Create B2B Centers Table
CREATE TABLE IF NOT EXISTS public.b2b_centers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  district TEXT NOT NULL,
  location TEXT,
  phone TEXT,
  "altPhone" TEXT,
  contactPerson TEXT,
  designation TEXT,
  email TEXT,
  link TEXT,
  status TEXT DEFAULT 'New',
  priority TEXT DEFAULT 'Medium',
  "lastContact" TEXT,
  "referredStudents" INTEGER DEFAULT 0,
  "enrolledStudents" INTEGER DEFAULT 0,
  "commissionRate" INTEGER DEFAULT 5000,
  "commissionPaid" INTEGER DEFAULT 0,
  notes JSONB DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create B2B Students Table
CREATE TABLE IF NOT EXISTS public.b2b_students (
  id TEXT PRIMARY KEY,
  "centerId" TEXT,
  "centerName" TEXT,
  district TEXT,
  name TEXT NOT NULL,
  phone TEXT,
  "targetCountry" TEXT DEFAULT 'South Korea',
  program TEXT,
  "ieltsScore" TEXT,
  stage TEXT DEFAULT 'Inquiry',
  "createdAt" TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Enable Row Level Security (RLS) & Public Access Policies
ALTER TABLE public.b2b_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.b2b_students ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read/write access to centers"
  ON public.b2b_centers FOR ALL
  USING (true) WITH CHECK (true);

CREATE POLICY "Allow public read/write access to students"
  ON public.b2b_students FOR ALL
  USING (true) WITH CHECK (true);

-- 4. Enable Realtime Replication for Live Sync
ALTER PUBLICATION supabase_realtime ADD TABLE public.b2b_centers;
ALTER PUBLICATION supabase_realtime ADD TABLE public.b2b_students;
