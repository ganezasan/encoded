from snovault import (
    calculated_property,
    collection,
    load_schema,
)
from snovault.util import try_to_get_field_from_item_with_skip_calculated_first
from .base import Item


def report_quality_metric(request, file_objects, quality_metric_definition):
    quality_metrics_report = {quality_metric_definition['report_name']: []}
    for f_obj in file_objects:
        if any(
            (
                f_obj[k] != quality_metric_definition['file_filters'][k]
                and quality_metric_definition['file_filters'][k] not in f_obj[k]
            )
            for k in quality_metric_definition['file_filters']
        ):
            continue
        for qm in f_obj.get('quality_metrics', []):
            qm_obj = request.embed(qm, '@@object')
            if any(
                (
                    qm_obj[k] != quality_metric_definition['quality_metric_filters'][k]
                    and quality_metric_definition['quality_metric_filters'][k] not in qm_obj[k]
                )
                for k in quality_metric_definition['quality_metric_filters']
            ):
                continue
            qm_value = qm_obj[quality_metric_definition['quality_metric_name']]
            quality_metrics_report[
                quality_metric_definition['report_name']
            ].append(qm_value)
        # The following two lines are for test only
        f_obj['award_rfa'] = request.embed(f_obj['award'], '@@object')['rfa']
        f_obj['target'] = 'test_target'
        quality = []
        for standard in quality_metric_definition.get('standards', []):
            if any(
                (
                    f_obj[k] != standard['standard_filters'][k]
                    and f_obj[k] not in standard['standard_filters'][k]
                )
                for k in standard['standard_filters']
            ):
                continue
            for v in quality_metrics_report[
                quality_metric_definition['report_name']
            ]:
                # The following order matters and depends a lot on the schema
                # definition. This might not be a good coding practice and
                # and to be improved.
                for level in [
                    'pass',
                    'warning',
                    'not_compliant',
                    'error',
                ]:
                    if v > standard[level]:
                        quality.append(level)
                        break
        if quality:
            quality_metrics_report[
                quality_metric_definition['report_name'] + '_quality'
            ] = quality
    return quality_metrics_report


@collection(
    name='analyses',
    unique_key='accession',
    properties={
        'title': 'Analyses',
        'description': 'Listing of analysis',
    })
class Analysis(Item):
    item_type = 'analysis'
    schema = load_schema('encoded:schemas/analysis.json')
    name_key = 'accession'
    embedded = [
        'files',
        'files.quality_metrics',
        'pipeline_labs',
    ]

    @calculated_property(schema={
        "title": "Datasets",
        "description": "Datasets the analysis belongs to.",
        "comment": "Do not submit. This field is calculated from files in this analysis.",
        "type": "array",
        "notSubmittable": True,
        "uniqueItems": True,
        "items": {
            "title": "Dataset",
            "description": "The dataset the analysis belongs to.",
            "type": "string",
            "linkTo": "Dataset"
        }
    })
    def datasets(self, request, files):
        return sorted({
            dataset
            for dataset in [
                try_to_get_field_from_item_with_skip_calculated_first(
                    request, 'dataset', f
                )
                for f in files
            ]
            if dataset is not None
        })

    file_schema = load_schema(
        'encoded:schemas/file.json'
    )

    @calculated_property(schema={
        "title": "Assembly",
        "description": "A genome assembly on which this analysis is performed.",
        "comment": "Do not submit. This field is calculated from files in this analysis.",
        "type": "string",
        "notSubmittable": True,
        "enum": ["mixed", *file_schema["properties"]["assembly"]["enum"]],
    })
    def assembly(self, request, files):
        assemblies = {
            assembly
            for assembly in [
                try_to_get_field_from_item_with_skip_calculated_first(
                    request, 'assembly', f
                )
                for f in files
            ]
            if assembly is not None
        }
        if len(assemblies) > 1:
            return 'mixed'
        if len(assemblies) == 1:
            return assemblies.pop()
        if len(assemblies) < 1:
            return

    @calculated_property(schema={
        "title": "Genome Annotation",
        "description": "A genome annotation on which this analysis is performed.",
        "comment": "Do not submit. This field is calculated from files in this analysis.",
        "type": "string",
        "notSubmittable": True,
        "enum": ["mixed", *file_schema["properties"]["genome_annotation"]["enum"]],
    })
    def genome_annotation(self, request, files):
        genome_annotations = {
            genome_annotation
            for genome_annotation in [
                try_to_get_field_from_item_with_skip_calculated_first(
                    request, 'genome_annotation', f
                )
                for f in files
            ]
            if genome_annotation is not None
        }
        if len(genome_annotations) > 1:
            return 'mixed'
        if len(genome_annotations) == 1:
            return genome_annotations.pop()
        if len(genome_annotations) < 1:
            return

    @calculated_property(
        define=True,
        schema={
            "title": "Pipelines",
            "description": "A list of pipelines used to generate this analysis.",
            "comment": "Do not submit. This field is calculated from files in this analysis.",
            "type": "array",
            "notSubmittable": True,
            "items": {
                "type": "string",
                "linkTo": "Pipeline"
            }
        }
    )
    def pipelines(self, request, files):
        pipelines = set()
        for f in files:
            file_object = request.embed(
                f,
                '@@object_with_select_calculated_properties?field=analysis_step_version'
            )
            if 'analysis_step_version' in file_object:
                analysis_step = request.embed(
                    file_object['analysis_step_version'],
                    '@@object?skip_calculated=true'
                )['analysis_step']
                pipelines |= set(
                    request.embed(
                        analysis_step,
                        '@@object_with_select_calculated_properties?field=pipelines'
                    ).get('pipelines', [])
                )
        return sorted(pipelines)

    @calculated_property(schema={
        "title": "Pipeline awards",
        "description": "A list of award bioproject phases to which pipelines "
                       "that used to generate this analysis belong to.",
        "comment": "Do not submit. This field is calculated from files in this analysis.",
        "type": "array",
        "notSubmittable": True,
        "items": {
            "type": "string"
        }
    })
    def pipeline_award_rfas(self, request, pipelines=[]):
        pipeline_award_rfas = set()
        for pipeline in pipelines:
            pipeline_object = request.embed(
                pipeline,
                '@@object?skip_calculated=true'
            )
            pipeline_award_rfas.add(
                request.embed(
                    pipeline_object['award'],
                    '@@object?skip_calculated=true'
                )['rfa']
            )
        return sorted(pipeline_award_rfas)

    @calculated_property(schema={
        "title": "Pipeline labs",
        "description": "A list of labs whose pipelines are used to generate this analysis.",
        "comment": "Do not submit. This field is calculated from files in this analysis.",
        "type": "array",
        "notSubmittable": True,
        "items": {
            "type": "string",
            "linkTo": "Lab"
        }
    })
    def pipeline_labs(self, request, pipelines=[]):
        return sorted({
            lab
            for lab in [
                try_to_get_field_from_item_with_skip_calculated_first(
                    request, 'lab', pipeline
                )
                for pipeline in pipelines
            ]
            if lab is not None
        })

    # Don't specify schema as this just overwrites the existing value
    @calculated_property()
    def quality_metrics_report(self, request, files, pipelines=[]):
        qm_defs = request.embed(
            pipelines[0], '@@object?skip_calculated=true'
        ).get('quality_metric_definitions', [])
        file_objects = [
            request.embed(
                f,
                '@@object_with_select_calculated_properties?field=quality_metrics'
            )
            for f in files
        ]
        quality_metrics_report = {}
        for qm_def in qm_defs:
            quality_metrics_report.update(
                report_quality_metric(
                    request=request,
                    file_objects=file_objects,
                    quality_metric_definition=qm_def,
                )
            )
        return quality_metrics_report
