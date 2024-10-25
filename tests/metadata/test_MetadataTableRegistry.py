import os
import sqlite3

from ml_experiment.DefinitionPart import DefinitionPart
from ml_experiment.metadata.MetadataTableRegistry import MetadataTableRegistry


def test_get_parts(tmp_path):
    """
    Test that get parts returns the parts correctly
    """
    # spin up metadata database
    df = DefinitionPart("test", base=str(tmp_path))
    df.add_property("a", 1)
    df.add_property("b", 2)
    df.add_property("c", 3)
    df.add_sweepable_property("seed", [1, 2, 3])
    df.commit()

    # find database file
    meta = MetadataTableRegistry()
    res_path = os.path.join(df.get_results_path(df.base_path), "metadata.db")

    ## initial test to get part name
    # get parts
    with sqlite3.connect(res_path) as con:
        cur = con.cursor()
        parts = meta.get_parts(cur)

        assert parts == set(["test"])

    ## test adding another property
    # add another property
    df.add_sweepable_property("d", [4, 5, 6], assume_prior_value=4)
    df.commit()

    # get parts
    with sqlite3.connect(res_path) as con:
        cur = con.cursor()
        parts = meta.get_parts(cur)

        assert parts == set(["test"])

    ## test adding a second part
    # add another part
    df2 = DefinitionPart("test-2", base=str(tmp_path))
    df2.add_property("a", 1)
    df2.add_property("b", 2)
    df2.add_property("c", 3)
    df2.add_sweepable_property("seed", [1, 2, 3])
    df2.commit()

    # get parts
    with sqlite3.connect(res_path) as con:
        cur = con.cursor()
        parts = meta.get_parts(cur)

        assert parts == set(["test", "test-2"])

    ## test with a part with a lot of hyphens
    # add another part
    df3 = DefinitionPart("test-3-lot-of-hyphens-", base=str(tmp_path))
    df3.add_property("a", 1)
    df3.add_sweepable_property("seed", [1, 2, 3])
    df3.commit()

    # get parts
    with sqlite3.connect(res_path) as con:
        cur = con.cursor()
        parts = meta.get_parts(cur)

        assert parts == set(["test", "test-2", "test-3-lot-of-hyphens-"])
