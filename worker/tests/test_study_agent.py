from worker.app.agents.study_agent import StudyInput, generate_study_package


def test_generate_study_package_returns_core_outputs():
    output = generate_study_package(
        StudyInput(
            title="REST APIs",
            prompt="Focus on architecture and HTTP methods",
            material_text=(
                "REST API is an architectural style for web services. "
                "It uses HTTP methods such as GET, POST, PUT, and DELETE. "
                "REST systems are usually stateless and organized around resources. "
                "Students should understand resources, methods, status codes, and request structure."
            ),
        )
    )

    assert output.important_topics
    assert output.summary
    assert output.quiz
    assert output.study_plan
