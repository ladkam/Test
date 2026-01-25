#!/usr/bin/env python3
"""
Test script to identify issues with recipes, substitution, and planner.
"""
from app import app
from models import db, Recipe, WeeklyPlan, PlanRecipe
from datetime import date, timedelta
import json

def test_issues():
    """Test the reported issues."""
    with app.app_context():
        print("Testing Recipe Management Issues...\n")

        # Test 1: Check if recipes exist and can be retrieved
        print("1. Testing recipe retrieval...")
        recipes = Recipe.query.all()
        print(f"   Found {len(recipes)} recipes in database")

        if recipes:
            recipe = recipes[0]
            print(f"   Sample recipe ID: {recipe.id}")
            print(f"   Title: {recipe.title}")
            recipe_dict = recipe.to_dict()
            print(f"   Recipe dict keys: {list(recipe_dict.keys())}")
            print(f"   Has 'language' field: {'language' in recipe_dict}")
            print(f"   Has 'source_language' field: {'source_language' in recipe_dict}")
            print(f"   Source language value: {recipe_dict.get('source_language')}")
        else:
            print("   ⚠️  No recipes found in database!")

        # Test 2: Check /api/planner/add functionality
        print("\n2. Testing planner add functionality...")
        if recipes:
            try:
                recipe_id = recipes[0].id

                # Get Monday of current week
                today = date.today()
                monday = today - timedelta(days=today.weekday())
                print(f"   Current week starts: {monday}")

                # Find or create plan
                plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
                if not plan:
                    plan = WeeklyPlan(week_start_date=monday)
                    db.session.add(plan)
                    db.session.flush()
                    print(f"   Created new plan with ID: {plan.id}")
                else:
                    print(f"   Found existing plan with ID: {plan.id}")

                # Check if recipe already in plan
                existing = PlanRecipe.query.filter_by(plan_id=plan.id, recipe_id=recipe_id).first()
                if existing:
                    print(f"   Recipe already in plan, removing it for clean test...")
                    db.session.delete(existing)
                    db.session.commit()

                # Try to add recipe
                plan_recipe = PlanRecipe(
                    plan_id=plan.id,
                    recipe_id=recipe_id,
                    day_of_week=1,
                    meal_order=0,
                    servings=4
                )
                db.session.add(plan_recipe)
                db.session.commit()
                print(f"   ✅ Successfully added recipe to plan with {plan_recipe.servings} servings")

                # Clean up
                db.session.delete(plan_recipe)
                db.session.commit()
                print(f"   Cleaned up test data")

            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

        # Test 3: Check API key configuration for substitutions
        print("\n3. Testing API key configuration for substitutions...")
        from models import Settings as SettingsModel
        groq_key = SettingsModel.get('groq_api_key', '')
        mistral_key = SettingsModel.get('mistral_api_key', '')

        print(f"   Groq API Key set: {'Yes' if groq_key else 'No'}")
        print(f"   Mistral API Key set: {'Yes' if mistral_key else 'No'}")

        if groq_key:
            print(f"   Groq key (first 10 chars): {groq_key[:10]}...")
        if mistral_key:
            print(f"   Mistral key (first 10 chars): {mistral_key[:10]}...")

        if not groq_key and not mistral_key:
            print("   ⚠️  No API keys configured! Substitutions will fail.")
            print("   Please add API keys in the admin panel at /admin")

        # Test 4: Check for field name issues
        print("\n4. Checking for field name compatibility issues...")
        if recipes:
            recipe_dict = recipes[0].to_dict()
            expected_fields = ['title', 'content', 'ingredients', 'source_language']
            old_fields = ['title_translated', 'title_original', 'language']

            print("   Expected fields:")
            for field in expected_fields:
                status = '✅' if field in recipe_dict else '❌'
                print(f"     {status} {field}")

            print("   Old/deprecated fields (should NOT be present):")
            for field in old_fields:
                status = '⚠️ ' if field in recipe_dict else '✅'
                print(f"     {status} {field}")

        print("\n" + "="*60)
        print("Test Summary:")
        print("="*60)
        if not recipes:
            print("❌ No recipes in database - please import a recipe first")
        else:
            print("✅ Recipes can be retrieved")

        if not groq_key and not mistral_key:
            print("❌ No API keys configured - substitutions won't work")
        else:
            print("✅ At least one API key is configured")

        print("="*60)

if __name__ == '__main__':
    test_issues()
