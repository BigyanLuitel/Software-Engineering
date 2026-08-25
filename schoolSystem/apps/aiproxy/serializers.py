from rest_framework import serializers


class AssistantQuerySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    class_id = serializers.IntegerField()
    query_text = serializers.CharField()
    subject_id = serializers.IntegerField(required=False, allow_null=True)
    interaction_mode = serializers.CharField(default="chat")


class QuestionPaperSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    topic = serializers.CharField()
    difficulty = serializers.CharField()
    question_count = serializers.IntegerField(default=10)


class NLQuerySerializer(serializers.Serializer):
    query_text = serializers.CharField()