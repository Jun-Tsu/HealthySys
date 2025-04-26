-- Programs
INSERT INTO programs (program_id, name, description) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'TB Program', 'Tuberculosis treatment and prevention'),
('550e8400-e29b-41d4-a716-446655440001', 'Malaria Program', 'Malaria prevention and care'),
('550e8400-e29b-41d4-a716-446655440002', 'HIV Program', 'HIV/AIDS management');

-- Clients (contact is hashed with SHA-256)
INSERT INTO clients (client_id, first_name, last_name, dob, gender, contact, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440100', 'John', 'Doe', '1990-01-01', 'Male', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440101', 'Jane', 'Smith', '1985-05-15', 'Female', '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440102', 'Alice', 'Johnson', '1978-03-22', 'Female', '3b9f8e4f8c6b7d2e9a0b1c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440103', 'Bob', 'Williams', '1995-11-30', 'Male', '4f8e9d0c1b2a3f4e5d6c7a8b9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440104', 'Emma', 'Brown', '1982-07-14', 'Female', '5a9f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7a8b9', '2025-04-27 10:00:00');

-- Enrollments
INSERT INTO enrollments (enrollment_id, client_id, program_id, enrollment_date) VALUES
('550e8400-e29b-41d4-a716-446655440200', '550e8400-e29b-41d4-a716-446655440100', '550e8400-e29b-41d4-a716-446655440000', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440201', '550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440202', '550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440002', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440203', '550e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440000', '2025-04-27 10:00:00'),
('550e8400-e29b-41d4-a716-446655440204', '550e8400-e29b-41d4-a716-446655440104', '550e8400-e29b-41d4-a716-446655440001', '2025-04-27 10:00:00');