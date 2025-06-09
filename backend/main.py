# backend/main.py
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os

# Create FastAPI app
app = FastAPI(
    title="WebMarket API",
    description="Professional template marketplace API",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI at /api/docs
    redoc_url="/api/redoc"  # ReDoc at /api/redoc
)

# CORS middleware - allows your frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (your frontend)
# Make sure the path exists
frontend_path = "../frontend"
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# Pydantic models for request/response validation
class Template(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str
    author: str
    image_url: str
    downloads: int
    rating: float
    created_at: str
    tags: List[str] = []


class CartItem(BaseModel):
    id: int
    template_id: int
    template: Template
    quantity: int
    added_at: str


class CartAddRequest(BaseModel):
    template_id: int


class SearchResponse(BaseModel):
    query: str
    category: Optional[str]
    results: List[Template]
    total: int


# Sample template data - matches your frontend
templates_db = [
    {
        "id": 1,
        "title": "ModernShop Pro",
        "description": "A fully responsive e-commerce template built with the latest technologies. Features include product filtering, shopping cart, payment integration, and a beautiful admin dashboard. Perfect for launching your online store quickly and professionally.",
        "price": 89.0,
        "category": "E-commerce",
        "author": "TechStudio",
        "image_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400",
        "downloads": 1250,
        "rating": 4.8,
        "created_at": "2024-01-15T10:00:00Z",
        "tags": ["responsive", "ecommerce", "modern", "dashboard"]
    },
    {
        "id": 2,
        "title": "Creative Portfolio",
        "description": "Stunning portfolio template for creatives, designers, and artists. Showcases your work with beautiful galleries, smooth animations, and mobile-first design.",
        "price": 69.0,
        "category": "Portfolio",
        "author": "DesignLab",
        "image_url": "https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?w=400",
        "downloads": 890,
        "rating": 4.9,
        "created_at": "2024-01-10T14:30:00Z",
        "tags": ["portfolio", "creative", "gallery", "animation"]
    },
    {
        "id": 3,
        "title": "Business Suite",
        "description": "Complete business website solution with multiple page layouts, contact forms, team sections, and service pages. Perfect for consulting, agencies, and corporate websites.",
        "price": 129.0,
        "category": "Business",
        "author": "ProDevs",
        "image_url": "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=400",
        "downloads": 567,
        "rating": 4.7,
        "created_at": "2024-01-05T09:15:00Z",
        "tags": ["business", "corporate", "professional", "multi-page"]
    },
    {
        "id": 4,
        "title": "Tech Startup Kit",
        "description": "Modern startup landing page with hero sections, feature highlights, pricing tables, and testimonials. Built for SaaS companies and tech startups.",
        "price": 149.0,
        "category": "Landing Page",
        "author": "CodeCraft",
        "image_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400",
        "downloads": 723,
        "rating": 4.6,
        "created_at": "2024-01-08T16:45:00Z",
        "tags": ["startup", "saas", "landing", "modern"]
    },
    {
        "id": 5,
        "title": "Restaurant Pro",
        "description": "Elegant restaurant website with menu displays, reservation system, gallery, and contact information. Perfect for restaurants, cafes, and food businesses.",
        "price": 79.0,
        "category": "Restaurant",
        "author": "WebMasters",
        "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400",
        "downloads": 445,
        "rating": 4.5,
        "created_at": "2024-01-12T11:20:00Z",
        "tags": ["restaurant", "food", "menu", "elegant"]
    },
    {
        "id": 6,
        "title": "Blog Master",
        "description": "Clean and minimal blog template with article layouts, author pages, categories, and search functionality. Perfect for personal blogs and content creators.",
        "price": 49.0,
        "category": "Blog",
        "author": "ContentPro",
        "image_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=400",
        "downloads": 892,
        "rating": 4.4,
        "created_at": "2024-01-18T13:10:00Z",
        "tags": ["blog", "minimal", "content", "clean"]
    }
]

# Cart storage (in production, this would be in a database)
cart_db = []

# Categories data
categories = [
    {"id": 1, "name": "E-commerce", "count": 48, "description": "Online store templates"},
    {"id": 2, "name": "Portfolio", "count": 36, "description": "Showcase your work"},
    {"id": 3, "name": "Business", "count": 52, "description": "Professional websites"},
    {"id": 4, "name": "Landing Page", "count": 29, "description": "Marketing pages"},
    {"id": 5, "name": "Restaurant", "count": 18, "description": "Food & dining"},
    {"id": 6, "name": "Blog", "count": 24, "description": "Content websites"}
]


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "WebMarket API is running!",
        "version": "1.0.0",
        "docs": "/api/docs",
        "frontend": "/static/index.html"
    }


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Templates endpoints
@app.get("/api/templates", response_model=dict)
async def get_templates(
        category: Optional[str] = None,
        limit: int = Query(default=10, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        sort_by: str = Query(default="downloads", regex="^(downloads|rating|price|created_at)$"),
        order: str = Query(default="desc", regex="^(asc|desc)$")
):
    """Get all templates with filtering, pagination, and sorting"""
    filtered_templates = templates_db.copy()

    # Filter by category
    if category:
        filtered_templates = [t for t in filtered_templates if t["category"].lower() == category.lower()]

    # Sort templates
    reverse = order == "desc"
    if sort_by == "created_at":
        filtered_templates.sort(key=lambda x: x["created_at"], reverse=reverse)
    else:
        filtered_templates.sort(key=lambda x: x[sort_by], reverse=reverse)

    # Pagination
    total = len(filtered_templates)
    paginated_templates = filtered_templates[offset:offset + limit]

    return {
        "templates": paginated_templates,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@app.get("/api/templates/{template_id}", response_model=Template)
async def get_template(template_id: int):
    """Get a specific template by ID"""
    template = next((t for t in templates_db if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.get("/api/templates/category/{category}")
async def get_templates_by_category(category: str, limit: int = 20):
    """Get templates by category"""
    filtered_templates = [t for t in templates_db if t["category"].lower() == category.lower()]
    return {
        "category": category,
        "templates": filtered_templates[:limit],
        "total": len(filtered_templates)
    }


@app.get("/api/categories")
async def get_categories():
    """Get all available categories"""
    return {"categories": categories}


# Search endpoints
@app.get("/api/search", response_model=SearchResponse)
async def search_templates(
        q: str = Query(..., min_length=1, description="Search query"),
        category: Optional[str] = None,
        min_price: Optional[float] = Query(None, ge=0),
        max_price: Optional[float] = Query(None, ge=0),
        min_rating: Optional[float] = Query(None, ge=0, le=5)
):
    """Search templates by title, description, or tags"""
    results = []
    query_lower = q.lower()

    for template in templates_db:
        # Search in title, description, and tags
        if (query_lower in template["title"].lower() or
                query_lower in template["description"].lower() or
                any(query_lower in tag.lower() for tag in template.get("tags", []))):

            # Apply filters
            if category and template["category"].lower() != category.lower():
                continue
            if min_price is not None and template["price"] < min_price:
                continue
            if max_price is not None and template["price"] > max_price:
                continue
            if min_rating is not None and template["rating"] < min_rating:
                continue

            results.append(template)

    return SearchResponse(
        query=q,
        category=category,
        results=results,
        total=len(results)
    )


# Cart endpoints
@app.get("/api/cart")
async def get_cart():
    """Get user's cart items"""
    total_price = sum(item["template"]["price"] * item["quantity"] for item in cart_db)
    return {
        "items": cart_db,
        "total_items": len(cart_db),
        "total_price": total_price
    }


@app.post("/api/cart/add")
async def add_to_cart(request: CartAddRequest):
    """Add template to cart"""
    template = next((t for t in templates_db if t["id"] == request.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check if already in cart
    existing_item = next((item for item in cart_db if item["template_id"] == request.template_id), None)
    if existing_item:
        existing_item["quantity"] += 1
        return {"message": "Quantity updated", "item": existing_item}

    cart_item = {
        "id": len(cart_db) + 1,
        "template_id": request.template_id,
        "template": template,
        "quantity": 1,
        "added_at": datetime.now().isoformat()
    }
    cart_db.append(cart_item)

    return {"message": "Template added to cart", "item": cart_item}


@app.put("/api/cart/{item_id}")
async def update_cart_item(item_id: int, quantity: int = Query(..., ge=1, le=10)):
    """Update cart item quantity"""
    item = next((item for item in cart_db if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item["quantity"] = quantity
    return {"message": "Cart item updated", "item": item}


@app.delete("/api/cart/{item_id}")
async def remove_from_cart(item_id: int):
    """Remove item from cart"""
    global cart_db
    original_length = len(cart_db)
    cart_db = [item for item in cart_db if item["id"] != item_id]

    if len(cart_db) == original_length:
        raise HTTPException(status_code=404, detail="Cart item not found")

    return {"message": "Item removed from cart"}


@app.delete("/api/cart/clear")
async def clear_cart():
    """Clear all items from cart"""
    global cart_db
    cart_db = []
    return {"message": "Cart cleared"}


# Trending and featured endpoints
@app.get("/api/templates/trending")
async def get_trending_templates(limit: int = 5):
    """Get trending templates (most downloaded)"""
    trending = sorted(templates_db, key=lambda x: x["downloads"], reverse=True)[:limit]
    return {"trending": trending}


@app.get("/api/templates/featured")
async def get_featured_templates(limit: int = 3):
    """Get featured templates (highest rated)"""
    featured = sorted(templates_db, key=lambda x: x["rating"], reverse=True)[:limit]
    return {"featured": featured}


# Stats endpoint
@app.get("/api/stats")
async def get_stats():
    """Get marketplace statistics"""
    total_templates = len(templates_db)
    total_downloads = sum(t["downloads"] for t in templates_db)
    avg_rating = sum(t["rating"] for t in templates_db) / total_templates if total_templates > 0 else 0

    return {
        "total_templates": total_templates,
        "total_downloads": total_downloads,
        "average_rating": round(avg_rating, 2),
        "categories": len(categories)
    }


# Serve frontend
@app.get("/frontend")
async def serve_frontend():
    """Serve the frontend HTML file"""
    frontend_file = "../frontend/index.html"
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")


# Run the server
if __name__ == "__main__":
    print("🚀 Starting WebMarket API Server...")
    print("📖 API Documentation: http://localhost:8000/api/docs")
    print("🌐 Frontend: http://localhost:8000/frontend")
    print("❤️  Health Check: http://localhost:8000/api/health")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )