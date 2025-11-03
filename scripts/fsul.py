import argparse
import pprint
import logging
import yaml
import os

import LIMS2DB.objectsDB.process_categories as pc_cg
import LIMS2DB.utils as lutils

from LIMS2DB.classes import Process
from LIMS2DB.flowcell_sql import create_lims_data_obj, upload_to_couch
from genologics_sql.utils import get_session

from sqlalchemy import text


def main(args):

    with open(args.conf) as conf_file:
        conf = yaml.safe_load(conf_file)
    couch = lutils.load_couch_server(conf)

    mainlog = get_logger('fsullogger')
    db_session = get_session()
    query = "select distinct pro.* from container ct \
                inner join containerplacement cp on ct.containerid=cp.containerid \
                inner join processiotracker piot on piot.inputartifactid=cp.processartifactid \
                inner join process pro on pro.processid=piot.processid \
                where pro.typeid in ({seq_type_ids}) and ct.name='{ct_name}';".format(seq_type_ids=",".join(list(pc_cg.SEQUENCING.keys())), ct_name=args.flowcell)
    seq_steps = db_session.query(Process).from_statement(text(query)).all()

    for step in seq_steps:
        for udf in step.udfs:
            if udf.udfname == "Run ID":
                fcid = udf.udfvalue

        # generate the lims_data dict key
        lims_data = create_lims_data_obj(db_session, step)
        if args.test:
            pp = pprint.pprint(lims_data)
        else:
            mainlog.info("updating {}".format(fcid))
            # update the couch right couch document
            upload_to_couch(couch, fcid, lims_data, step)


def get_logger(name):
    mainlog = logging.getLogger(name)
    mainlog.setLevel(level=logging.ERROR)
    mfh = logging.StreamHandler()
    mft = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    mfh.setFormatter(mft)
    mainlog.addHandler(mfh)
    return mainlog


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", dest="flowcell", required=True)
    parser.add_argument("-x", dest="test", action='store_true')
    parser.add_argument("-c", dest="conf", default="{0}/conf/LIMS2DB/post_process.yaml".format(os.environ["HOME"]))
    args = parser.parse_args()
    main(args)
