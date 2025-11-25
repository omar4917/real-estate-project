from collections import defaultdict, deque

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView

from .models import Category, Property
from .serializers import CategorySerializer, PropertyDetailSerializer, PropertySummarySerializer

# API endpoints (public)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class PropertyListView(generics.ListAPIView):
    queryset = (
        Property.objects.filter(status=Property.STATUS_ACTIVE)
        .select_related("category", "category__parent")
        .all()
    )
    serializer_class = PropertySummarySerializer
    permission_classes = [AllowAny]


class PropertyDetailView(generics.RetrieveAPIView):
    lookup_field = "slug"
    queryset = Property.objects.select_related("category", "category__parent").all()
    serializer_class = PropertyDetailSerializer
    permission_classes = [AllowAny]


class PropertyRecommendationsView(APIView):
    permission_classes = [AllowAny]
    cache_timeout = 300  # seconds

    def get_category_graph(self):
        graph = cache.get("category_graph")
        if graph:
            return graph

        graph = defaultdict(list)
        categories = Category.objects.all().values("id", "parent_id")
        for cat in categories:
            parent_id = cat["parent_id"]
            if parent_id:
                graph[parent_id].append(cat["id"])
        cache.set("category_graph", graph, timeout=self.cache_timeout)
        return graph

    def dfs_collect(self, graph, start_id):
        visited = set()
        stack = deque([start_id])
        result = []
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            result.append(node)
            for child in graph.get(node, []):
                stack.append(child)
        return result

    def get(self, request, slug):
        property_obj = get_object_or_404(
            Property.objects.select_related("category"),
            slug=slug,
            status=Property.STATUS_ACTIVE,
        )
        category_id = property_obj.category_id
        graph = self.get_category_graph()
        category_ids = self.dfs_collect(graph, category_id)

        recommendations = (
            Property.objects.filter(status=Property.STATUS_ACTIVE, category_id__in=category_ids)
            .exclude(id=property_obj.id)
            .select_related("category")
            .order_by("-created_at")[:10]
        )
        serializer = PropertySummarySerializer(recommendations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["properties"] = (
            Property.objects.filter(status=Property.STATUS_ACTIVE)
            .select_related("category")
            .order_by("-created_at")[:12]
        )
        return ctx


class PropertyPageView(TemplateView):
    template_name = "property_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = kwargs.get("slug")
        prop = get_object_or_404(
            Property.objects.select_related("category"),
            slug=slug,
            status=Property.STATUS_ACTIVE,
        )
        ctx["property"] = prop
        return ctx
