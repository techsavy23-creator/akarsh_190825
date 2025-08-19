from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Store, StoreReport, ReportStatus
from .serializers import StoreSerializer, ReportSerializer
from .helper import trigger_report_combined


class StoreViewSet(ModelViewSet):
    """
    CRUD API for Stores
    """
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class ReportViewSet(ModelViewSet):
    """
    API for handling uptime/downtime reports.
    
    Endpoints:
    - POST /reports/trigger_report/ : create and start a report
    - GET  /reports/get_report/<id>/ : fetch the status/result of a report
    """
    queryset = StoreReport.objects.all()
    serializer_class = ReportSerializer

    @action(detail=False, methods=["post"], url_path="trigger_report")
    def trigger_report(self, request):
        """
        Trigger a new report.
        Creates a StoreReport with PENDING status,
        then generates the report CSV and updates status to COMPLETE.
        """
        # Create report record in DB
        report = StoreReport.objects.create(status=ReportStatus.PENDING)

        # Generate CSV + mark COMPLETE
        trigger_report_combined(report)

        return Response(
            {"report_id": report.id},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="get_report")
    def get_report(self, request, pk=None):
        """
        Check the status of a report by its ID.
        - If still running, return {"status": "Running"}.
        - If complete, return {"status": "Complete", "report_url": "..."}.
        """
        try:
            report = StoreReport.objects.get(pk=pk)
        except StoreReport.DoesNotExist:
            return Response(
                {"error": "Report not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if report.status == ReportStatus.PENDING:
            return Response({"status": "Running"})

        return Response(
            {
                "status": "Complete",
                "report_url": request.build_absolute_uri(report.report_url.url),
            }
        )
