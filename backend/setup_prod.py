#!/usr/bin/env python3
"""
Setup script for production deployment.
Usage: python setup_prod.py postgresql+asyncpg://user:pass@host:port/db
"""
import sys
import os
import subprocess
import tempfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd=None):
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_prod.py <DATABASE_URL>")
        print("")
        print("Example:")
        print("  python setup_prod.py postgresql+asyncpg://postgres:password@db.xxxxx.supabase.co:6543/postgres")
        sys.exit(1)

    db_url = sys.argv[1]

    print("=" * 60)
    print("BOLETA SAAS - PRODUCTION SETUP")
    print("=" * 60)

    # 1. Install/verify dependencies
    print("\n[1/4] Installing dependencies...")
    run(["pip", "install", "-r", "requirements.txt"])

    # 2. Write .env with database URL
    print("\n[2/4] Configuring environment...")
    env_path = ".env"
    with open(env_path, "w") as f:
        f.write(f"DATABASE_URL={db_url}\n")
        f.write("ENVIRONMENT=production\n")
    print(f"  Created .env with DATABASE_URL")

    # 3. Run migrations
    print("\n[3/4] Running database migrations...")
    os.environ["DATABASE_URL"] = db_url
    os.environ["ENVIRONMENT"] = "production"
    run(["alembic", "upgrade", "head"])

    # 4. Seed data (super admin + system settings)
    print("\n[4/4] Seeding initial data...")
    run(["python", "seed.py"])

    print("\n" + "=" * 60)
    print("SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Deploy backend to Railway")
    print("     railway up --service backend-api")
    print("  2. Deploy frontend to Vercel")
    print("     cd frontend && vercel --prod")
    print("")
