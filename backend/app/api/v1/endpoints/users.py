"""
User profile endpoints for managing user data.
"""

from fastapi import APIRouter, Depends, Request

from app.core.exceptions import NotFoundError
from app.core.logging_config import get_logger
from app.dependencies import get_access_token, get_current_user
from app.schemas.auth import MessageResponse, UserResponse
from app.schemas.user import DeleteAccountRequest, UpdateProfileRequest, UserProfileResponse
from app.services.supabase_client import SupabaseService, get_supabase_service

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Get Profile",
    description="Get the current user's profile",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Profile not found"},
    },
)
async def get_profile(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> UserProfileResponse:
    """
    Get the current user's profile.

    Retrieves profile data from the profiles table, including
    additional user metadata not stored in auth.users.

    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        supabase: Supabase service instance

    Returns:
        UserProfileResponse with profile data
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        f"Get profile request for user: {current_user.id}",
        extra={"request_id": request_id, "user_id": current_user.id},
    )

    # Try to get profile from profiles table
    profile = await supabase.get_profile(current_user.id)

    if profile:
        return UserProfileResponse(
            id=profile["id"],
            email=profile["email"],
            full_name=profile.get("full_name"),
            avatar_url=profile.get("avatar_url"),
            created_at=profile["created_at"],
            updated_at=profile.get("updated_at"),
        )

    # Fall back to auth user data if profile doesn't exist
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        updated_at=None,
    )


@router.patch(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update Profile",
    description="Update the current user's profile",
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def update_profile(
    request: Request,
    data: UpdateProfileRequest,
    current_user: UserResponse = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> UserProfileResponse:
    """
    Update the current user's profile.

    Updates profile data in the profiles table.
    Only provided fields will be updated.

    Args:
        request: FastAPI request object
        data: Profile update data
        current_user: Current authenticated user
        supabase: Supabase service instance

    Returns:
        UserProfileResponse with updated profile data
    """
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        f"Update profile request for user: {current_user.id}",
        extra={"request_id": request_id, "user_id": current_user.id},
    )

    # Build update dict with only provided fields
    update_data = {}
    if data.full_name is not None:
        update_data["full_name"] = data.full_name
    if data.avatar_url is not None:
        update_data["avatar_url"] = data.avatar_url

    if update_data:
        updated_profile = await supabase.update_profile(current_user.id, update_data)

        if updated_profile:
            logger.info(
                f"Profile updated for user: {current_user.id}",
                extra={"request_id": request_id, "user_id": current_user.id},
            )

            return UserProfileResponse(
                id=updated_profile["id"],
                email=updated_profile["email"],
                full_name=updated_profile.get("full_name"),
                avatar_url=updated_profile.get("avatar_url"),
                created_at=updated_profile["created_at"],
                updated_at=updated_profile.get("updated_at"),
            )

    # Return current user data if no updates made
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        updated_at=None,
    )


@router.delete(
    "/account",
    response_model=MessageResponse,
    summary="Delete Account",
    description="Permanently delete the current user's account",
    responses={
        200: {"description": "Account deleted successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def delete_account(
    request: Request,
    data: DeleteAccountRequest,
    current_user: UserResponse = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> MessageResponse:
    """
    Delete the current user's account.

    This action is permanent and cannot be undone.
    Requires explicit confirmation by setting confirm=true.

    Args:
        request: FastAPI request object
        data: Deletion confirmation data
        current_user: Current authenticated user
        supabase: Supabase service instance

    Returns:
        MessageResponse confirming deletion
    """
    request_id = getattr(request.state, "request_id", None)

    if not data.confirm:
        logger.warning(
            f"Account deletion not confirmed for user: {current_user.id}",
            extra={"request_id": request_id, "user_id": current_user.id},
        )
        return MessageResponse(
            message="Account deletion requires confirmation",
            success=False,
        )

    logger.warning(
        f"Account deletion request for user: {current_user.id}",
        extra={"request_id": request_id, "user_id": current_user.id},
    )

    await supabase.delete_user(current_user.id)

    logger.info(
        f"Account deleted for user: {current_user.id}",
        extra={"request_id": request_id, "user_id": current_user.id},
    )

    return MessageResponse(
        message="Account deleted successfully",
        success=True,
    )
