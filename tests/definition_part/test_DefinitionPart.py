from ml_experiment.definition_part import DefinitionPart


def test_add_sweepable_property():
    builder = DefinitionPart('qrc')
    builder.add_sweepable_property('key_1', [1, 2, 3])

    for i in range(1, 4):
        builder.add_property('key_2', i)
