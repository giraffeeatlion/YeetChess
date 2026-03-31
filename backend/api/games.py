"""
Game Endpoints
/games (create, list), /games/{game_id} (get single game)
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..models.game import Game
from ..schemas.game import GameCreate, GameResponse, GameListResponse
from ..utils.security import extract_user_id_from_token, verify_token

router = APIRouter(prefix="/games", tags=["games"])


async def get_current_user_from_header(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract and validate current user from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    payload = verify_token(token, settings.jwt_secret_key, settings.jwt_algorithm)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = extract_user_id_from_token(
        token,
        settings.jwt_secret_key,
        settings.jwt_algorithm
    )
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    stmt = select(User).where(User.id == user_id)
    user = await db.scalar(stmt)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_create: GameCreate,
    current_user: User = Depends(get_current_user_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new game.
    
    opponent_type can be:
    - "random": Find a random opponent (currently assigns a placeholder)
    - "bot": Play against an AI bot (bot_id = 0 as placeholder)
    """
    # Determine opponent ID
    if game_create.opponent_type == "random":
        # For Phase 2: assign a placeholder opponent (in Phase 5, this will be a matchmaking queue)
        # Using user_id = 2 as a placeholder (make sure this user exists or handle gracefully)
        opponent_id = 2
        stmt = select(User).where(User.id == opponent_id)
        opponent = await db.scalar(stmt)
        if not opponent and current_user.id != opponent_id:
            # Create a test opponent if it doesn't exist
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No opponents available (random matchmaking not yet implemented)"
            )
    elif game_create.opponent_type == "bot":
        # Bot placeholder: For Phase 2, use any available user except current user
        # In Phase 5, this will spawn an actual bot AI worker
        # Try to find any other user
        stmt = select(User).where(User.id != current_user.id)
        opponent = await db.scalar(stmt)
        if opponent:
            opponent_id = opponent.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No bot player available (bot implementation pending Phase 5)"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid opponent_type"
        )
    
    if opponent_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot play against yourself"
        )
    
    # Create game (current user is white)
    game = Game(
        white_id=current_user.id,
        black_id=opponent_id
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)
    
    return GameResponse.model_validate(game)


@router.get("/", response_model=GameListResponse)
async def list_games(
    current_user: User = Depends(get_current_user_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    List all games for the current user (as white or black).
    """
    stmt = select(Game).where(
        or_(
            Game.white_id == current_user.id,
            Game.black_id == current_user.id
        )
    ).order_by(Game.created_at.desc())
    
    games = await db.scalars(stmt)
    game_list = list(games)
    
    return GameListResponse(
        games=[GameResponse.model_validate(g) for g in game_list],
        total=len(game_list)
    )


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single game by ID.
    """
    stmt = select(Game).where(Game.id == game_id)
    game = await db.scalar(stmt)
    
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    return GameResponse.model_validate(game)
