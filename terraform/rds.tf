# ══════════════════════════════════════════════════════════════════════════════
# RDS PostgreSQL — db.t3.micro Single-AZ (~$13/month, Free Tier eligible)
# ══════════════════════════════════════════════════════════════════════════════

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]

  tags = merge(var.tags, { Name = "${var.project_name}-db-subnet" })
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-db"

  # ── Engine ─────────────────────────────────────────────────────
  engine               = "postgres"
  engine_version       = "16.4"
  instance_class       = var.rds_instance_class
  parameter_group_name = "default.postgres16"

  # ── Storage ────────────────────────────────────────────────────
  allocated_storage     = 20
  max_allocated_storage = 50    # autoscaling up to 50GB
  storage_type          = "gp3"
  storage_encrypted     = true

  # ── Credentials (from Secrets Manager) ─────────────────────────
  db_name  = "procurement_db"
  username = "procurement"
  password = random_password.db_password.result

  # ── Network ────────────────────────────────────────────────────
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true    # Lambda is outside VPC — saves NAT Gateway ($35/mo)
  port                   = 5432

  # ── Availability ───────────────────────────────────────────────
  multi_az = false    # Single-AZ for cost savings — enable later if needed

  # ── Backup & Maintenance ───────────────────────────────────────
  backup_retention_period   = 7
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true
  copy_tags_to_snapshot     = true
  deletion_protection       = var.rds_deletion_protection
  skip_final_snapshot       = var.rds_skip_final_snapshot
  final_snapshot_identifier = var.rds_skip_final_snapshot ? null : "${var.project_name}-final-snapshot"

  # ── Monitoring ─────────────────────────────────────────────────
  performance_insights_enabled = false    # Free on db.t3.micro but limited

  tags = merge(var.tags, { Name = "${var.project_name}-db" })
}

# ── Generate a strong random password ────────────────────────────────────────

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%^&*()-_=+"
}
