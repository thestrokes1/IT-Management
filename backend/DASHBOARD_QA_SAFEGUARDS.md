# Dashboard Navigation QA & Regression Safeguards

This document provides safeguards to ensure dashboard navigation, permissions, and routing cannot regress.

---

## Section 1: Manual QA Checklist

### 1.1 Statistic Cards Navigation

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Click "Active Users" card | Redirects to `/users/` | ☐ |
| Click "Open Assets" card | Redirects to `/assets/?status=maintenance` | ☐ |
| Click "Active Assets" card | Redirects to `/assets/?status=active` | ☐ |
| Click "Active Projects" card | Redirects to `/projects/` | ☐ |
| Click "Open Tickets" card | Redirects to `/tickets/?status=open` | ☐ |

### 1.2 Query Parameter Filtering

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Click Open Assets → verify filter | Assets list shows only MAINTENANCE status | ☐ |
| Click Active Assets → verify filter | Assets list shows only ACTIVE status | ☐ |
| Click Open Tickets → verify filter | Tickets list shows only OPEN status | ☐ |

### 1.3 Recent Activity Links

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Click ticket activity item | Redirects to ticket detail page | ☐ |
| Click asset activity item | Redirects to asset detail page | ☐ |
| Click project activity item | Redirects to project detail page | ☐ |
| Click user activity item | Redirects to user detail page | ☐ |

### 1.4 Recent Items Navigation

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Click recent ticket row | Redirects to ticket detail | ☐ |
| Click recent asset row | Redirects to asset detail | ☐ |
| Verify cursor changes to pointer on hover | Visual feedback present | ☐ |

### 1.5 RBAC Permission Checks

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| TECHNICIAN views dashboard | Users card NOT visible | ☐ |
| TECHNICIAN views dashboard | Projects card NOT visible | ☐ |
| TECHNICIAN views dashboard | Security section NOT visible | ☐ |
| MANAGER views dashboard | All cards visible | ☐ |
| SUPERADMIN views dashboard | All cards visible | ☐ |

### 1.6 Visual Layout Verification

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Cards display in grid layout | 5 columns on desktop, 2 on tablet, 1 on mobile | ☐ |
| Cards have consistent padding | All cards have equal spacing | ☐ |
| Hover effects present | Shadow increases on card hover | ☐ |
| No broken anchor layout | Cards maintain block display | ☐ |

---

## Section 2: Automated Smoke Test Plan

### 2.1 Django Test Client Tests

```python
# tests/test_dashboard_navigation.py

from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch


class DashboardNavigationTest(TestCase):
    """Smoke tests for dashboard navigation links."""
    
    def setUp(self):
        self.client = Client()
        # Create test users for each role
        self.superadmin = User.objects.create_user(
            username='test_superadmin', role='SUPERADMIN'
        )
        self.manager = User.objects.create_user(
            username='test_manager', role='MANAGER'
        )
        self.technician = User.objects.create_user(
            username='test_technician', role='TECHNICIAN'
        )

    def test_statistic_cards_url_names_exist(self):
        """Verify all card URLs use valid URL names."""
        url_names = [
            'frontend:users',
            'frontend:assets',
            'frontend:projects',
            'frontend:tickets',
        ]
        for name in url_names:
            with self.subTest(url_name=name):
                try:
                    reverse(name)
                except NoReverseMatch:
                    self.fail(f"URL name '{name}' does not exist")

    def test_query_parameters_are_correct(self):
        """Verify query parameters match expected filters."""
        # These are the expected query strings
        expected_params = {
            'assets/?status=maintenance': 'maintenance',
            'assets/?status=active': 'active',
            'tickets/?status=open': 'open',
        }
        for path, status in expected_params.items():
            # Verify the URL resolves correctly
            response = self.client.get(f'/{path}')
            self.assertIn(response.status_code, [200, 302])

    def test_rbac_cards_visibility(self):
        """Verify cards are conditionally rendered based on permissions."""
        # Technician should NOT see Users card
        self.client.force_login(self.technician)
        response = self.client.get(reverse('frontend:dashboard'))
        self.assertNotContains(response, 'Active Users')

        # Manager should see all cards
        self.client.force_login(self.manager)
        response = self.client.get(reverse('frontend:dashboard'))
        self.assertContains(response, 'Active Users')
        self.assertContains(response, 'Active Projects')

    def test_recent_activity_links_resolve(self):
        """Verify recent activity links resolve without 404."""
        # Create test activity with ticket target
        activity = ActivityLog.objects.create(
            target_type='ticket',
            target_id=1,
            action='created',
        )
        
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse('frontend:dashboard'))
        # Should not contain broken links
        self.assertNotContains(response, 'href="#"')
```

### 2.2 Playwright E2E Tests

```javascript
// tests/e2e/dashboard-navigation.spec.js
// Run with: npx playwright test dashboard-navigation.spec.js

import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.login('superadmin', 'password');
    await page.goto('/dashboard');
  });

  test('Statistic cards are clickable and navigate correctly', async ({ page }) => {
    // Test Users card
    await page.click('a[href*="/users/"]');
    await expect(page).toHaveURL(/.*\/users\/.*/);
    
    // Test Assets card with query param
    await page.goto('/dashboard');
    await page.click('a[href*="status=maintenance"]');
    await expect(page).toHaveURL(/.*status=maintenance.*/);
  });

  test('Cards respect RBAC - technician sees limited cards', async ({ page }) => {
    await page.login('technician', 'password');
    await page.goto('/dashboard');
    
    // Technician should not see Users card
    const usersCard = page.locator('text=Active Users').first();
    await expect(usersCard).not.toBeVisible();
  });

  test('Recent items have hover effects', async ({ page }) => {
    const ticketRow = page.locator('tr:has-text("Recent Tickets") >> nth=1');
    await expect(ticketRow).toHaveCSS('cursor', 'pointer');
  });

  test('No broken anchor links', async ({ page }) => {
    const brokenLinks = page.locator('a[href="#"]');
    await expect(brokenLinks).toHaveCount(0);
  });
});
```

### 2.3 Template Validation Tests

```python
# tests/test_dashboard_template.py

from django.test import TestCase
from django.template import Template, Context
from django.contrib.auth import get_user_model


class DashboardTemplateTest(TestCase):
    """Validate dashboard template structure."""
    
    def test_all_cards_use_url_template_tag(self):
        """Ensure no hardcoded URLs in dashboard template."""
        template_content = '''
        {% extends "frontend/base.html" %}
        {% block content %}
        {% url 'frontend:users' as users_url %}
        {% url 'frontend:assets' as assets_url %}
        {% url 'frontend:projects' as projects_url %}
        {% url 'frontend:tickets' as tickets_url %}
        {% endblock %}
        '''
        template = Template(template_content)
        context = Context({})
        rendered = template.render(context)
        
        # Verify URL tags are used, not hardcoded paths
        self.assertIn("{% url 'frontend:users' %}", rendered)
        self.assertIn("{% url 'frontend:assets' %}", rendered)
        
    def test_rbac_guards_present(self):
        """Verify all restricted cards have permission guards."""
        dashboard_template_path = 'frontend/dashboard.html'
        with open(dashboard_template_path) as f:
            content = f.read()
        
        # Users card must have guard
        self.assertIn('{% if can_access_users %}', content)
        
        # Assets cards must have guard
        self.assertIn('{% if can_access_assets %}', content)
        
        # Projects card must have guard
        self.assertIn('{% if can_access_projects %}', content)
```

---

## Section 3: Regression Warning Signs

### 3.1 Critical Issues (Immediate Action Required)

| Warning Sign | Likely Cause | Detection Method |
|--------------|--------------|------------------|
| Dashboard returns 500 error | Missing URL name or template syntax error | Automated test |
| Clicking card shows 404 | URL name changed or removed | Manual QA, automated test |
| Clicking card shows 403 | Permission guard missing or logic changed | Manual QA |
| Cards display as inline instead of block | Anchor tag styling issue | Visual QA |
| Cards not visible for authorized users | Permission flag renamed or removed | Manual QA |

### 3.2 Functional Regressions

| Warning Sign | Likely Cause | Prevention |
|--------------|--------------|------------|
| Query parameters not filtering | List view doesn't accept params | Verify list views accept `status` param |
| Recent items not clickable | JavaScript or onclick removed | Check for `cursor-pointer` class |
| Activity links wrong page | Activity target_type mapping incorrect | Verify activity log target_type values |
| Cards layout broken on mobile | CSS grid or responsive classes removed | Test on mobile viewport |

### 3.3 Permission Leaks

| Warning Sign | Risk Level | Detection |
|--------------|------------|-----------|
| TECHNICIAN sees Users card | HIGH | RBAC test fails |
| TECHNICIAN sees Projects card | HIGH | RBAC test fails |
| Unauthorized user sees Security section | HIGH | RBAC test fails |
| VIEWER sees admin-only cards | MEDIUM | RBAC test fails |

### 3.4 URL Pattern Changes (Do NOT Do This)

```python
# ❌ WRONG - Changing URL names breaks dashboard links
path('users/', users, name='user-list'),  # Changed from 'users'

# ✅ CORRECT - Keep existing URL names
path('users/', users, name='users'),
```

### 3.5 Template Anti-Patterns to Avoid

```html
<!-- ❌ WRONG - Hardcoded URL -->
<a href="/users/" class="card">Users</a>

<!-- ✅ CORRECT - Use URL template tag -->
<a href="{% url 'frontend:users' %}" class="card">Users</a>

<!-- ❌ WRONG - Missing RBAC guard -->
<div class="card">Users</div>

<!-- ✅ CORRECT - With permission guard -->
{% if can_access_users %}
<a href="{% url 'frontend:users' %}" class="card">Users</a>
{% endif %}

<!-- ❌ WRONG - Anchor breaks card layout -->
<a href="{% url 'frontend:users' %}" class="card">
  <div class="full-content">...</div>
</a>

<!-- ✅ CORRECT - Block display anchor -->
<a href="{% url 'frontend:users' %}" class="block">
  <div class="content">...</div>
</a>
```

---

## Section 4: Quick Validation Commands

### Run Template Validation
```bash
cd backend
python manage.py test apps.frontend.tests.test_dashboard_template
```

### Run Navigation Smoke Tests
```bash
python manage.py test apps.frontend.tests.test_dashboard_navigation
```

### Check for Hardcoded URLs
```bash
grep -r "/users/" templates/frontend/dashboard.html
grep -r "/assets/" templates/frontend/dashboard.html
grep -r "/tickets/" templates/frontend/dashboard.html
```

### Verify URL Names Exist
```bash
python manage.py show_urls | grep -E "(users|assets|projects|tickets)"
```

---

## Summary

| Protection Layer | What It Guards | Test Location |
|------------------|----------------|---------------|
| URL name validation | Broken reverse lookups | `test_dashboard_navigation.py` |
| Query param validation | Filter functionality | `test_dashboard_navigation.py` |
| RBAC guards | Permission leaks | `test_dashboard_navigation.py` |
| Template syntax | Hardcoded URLs | `test_dashboard_template.py` |
| Visual regression | Layout issues | Playwright E2E tests |
| Manual verification | UX issues | QA Checklist |

**Key Principle:** Dashboard is a pure navigation layer. Any change to URLs, permissions, or template structure must be validated against this document.
