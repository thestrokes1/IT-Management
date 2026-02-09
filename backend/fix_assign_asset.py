"""Fix script for asset assignment issue."""

# Fix the asset_assign_to_user function
file_path = 'apps/frontend/views/assets.py'
with open(file_path, 'r') as f:
    content = f.read()

# Replace AssignAssetToSelf with AssignAsset in the asset_assign_to_user function
old_code = """    # Use the CQRS command to assign
    use_case = AssignAssetToSelf()
    try:
        result = use_case.execute(request.user, str(asset.asset_id), target_user.id)"""

new_code = """    # Use the CQRS command to assign - use AssignAsset for assigning to another user
    use_case = AssignAsset()
    try:
        result = use_case.execute(request.user, str(asset.asset_id), target_user.id)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print('Fixed asset_assign_to_user function - changed AssignAssetToSelf to AssignAsset')
else:
    print('Pattern not found, checking if already fixed...')
    if 'use_case = AssignAsset()' in content:
        print('Already fixed!')
