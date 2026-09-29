-- ====================================================================
-- AI-Based Power Line Pole Inspection and Maintenance Recommendation System
-- Database Schema (MySQL Compatible)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS power_line_inspection;
USE power_line_inspection;

-- --------------------------------------------------------------------
-- Table 1: poles
-- Stores electrical distribution/transmission pole asset information
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS poles (
    pole_id VARCHAR(50) PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    installation_date DATE,
    status VARCHAR(50) DEFAULT 'Normal' -- 'Normal', 'Warning', 'Critical', 'Maintenance Required'
);

-- --------------------------------------------------------------------
-- Table 2: inspections
-- Stores historical inspection records and AI defect detection outputs
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id INT AUTO_INCREMENT PRIMARY KEY,
    pole_id VARCHAR(50) NOT NULL,
    inspection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(255) NOT NULL,
    defect_type VARCHAR(100) NOT NULL,
    confidence DECIMAL(5, 2) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'HIGH', 'MEDIUM', 'LOW', 'NORMAL'
    recommendation TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending Review', -- 'Pending Review', 'Action Required', 'Completed'
    FOREIGN KEY (pole_id) REFERENCES poles(pole_id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------
-- Table 3: maintenance
-- Stores maintenance lifecycle tasks and repair tracking
-- Workflow stages: Pending -> Assigned -> In Progress -> Repaired -> Verified
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
    inspection_id INT NULL,
    pole_id VARCHAR(50) NOT NULL,
    action VARCHAR(255) NOT NULL,
    assigned_to VARCHAR(100),
    maintenance_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending', -- 'Pending', 'Assigned', 'In Progress', 'Repaired', 'Verified'
    remarks TEXT,
    FOREIGN KEY (pole_id) REFERENCES poles(pole_id) ON DELETE CASCADE,
    FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id) ON DELETE SET NULL
);

-- ====================================================================
-- Database Schema Ready for Live Inspection & Maintenance Records
-- ====================================================================

