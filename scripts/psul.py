import argparse
import pprint
import logging
import yaml
import os

from LIMS2DB.classes import ProjectSQL
import LIMS2DB.utils as lutils
from genologics_sql.utils import get_configuration, get_session
from genologics_sql.tables import Project as DBProject


def main(args):

    with open(args.conf, 'r') as conf_file:
        conf = yaml.safe_load(conf_file)
    couch = lutils.load_couch_server(conf)

    with open(args.oconf, 'r') as ocf:
        oconf = yaml.safe_load(ocf)['order_portal']

    mainlog = get_logger('psullogger')

    lims_db = get_session()
    host = get_configuration()['url']

    if args.name:
        pj_id = lims_db.query(DBProject.luid).filter(DBProject.name ==args.name).scalar()
    else:
        pj_id = args.pid

    P = ProjectSQL(lims_db, mainlog, pj_id, host, couch, oconf)

    if args.test:
        pp = pprint.pprint(P.obj)
    else:
        P.save()


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
    parser.add_argument("-p", dest="pid")
    parser.add_argument("-n", dest="name")
    parser.add_argument("-x", dest="test", action='store_true')
    parser.add_argument("-c", dest="conf", default="{0}/conf/LIMS2DB/post_process.yaml".format(os.environ["HOME"]))
    parser.add_argument("-oc", dest="oconf", default="{0}/conf/orderportal_cred.yaml".format(os.environ["HOME"]))
    args = parser.parse_args()
    if args.pid is None and args.name is None:
        raise argparse.ArgumentError("at least one of -p and -n is required")
    else:
        main(args)
