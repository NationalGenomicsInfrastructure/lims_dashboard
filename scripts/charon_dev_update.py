from ibmcloudant import CouchDbSessionAuthenticator, cloudant_v1
from ibm_cloud_sdk_core.api_exception import ApiException
import yaml
import argparse
import os


def main(args):
    with open(args.conf, 'r') as conf_f:
        conf = yaml.load(conf_f, Loader=yaml.SafeLoader)

    db_conf = conf["statusdb"]
    cloudant_auth = CouchDbSessionAuthenticator(
        db_conf["username"], db_conf["password"]
    )
    statusdb = cloudant_v1.CloudantV1(authenticator=cloudant_auth)
    statusdb.set_service_url(f"https://{db_conf['url']}")

    db_conf = conf["statusdbdev"]
    cloudant_auth_dev = CouchDbSessionAuthenticator(
        db_conf["username"], db_conf["password"]
    )
    statusdb_dev = cloudant_v1.CloudantV1(authenticator=cloudant_auth_dev)
    statusdb_dev.set_service_url(f"https://{db_conf['url']}")
    ids = []

    if "_" in args.project:
        pid = statusdb.post_view(
            db="charon",
            ddoc="project",
            view="name",
            key=args.project
            ).get_result()["rows"][0]["value"]
    else:
        pid = args.project

    pid_docid = statusdb.post_view(
        db="charon",
        ddoc="project",
        view="projectid",
        key=pid
        ).get_result()["rows"][0]["id"]
    ids.append(pid_docid)
    sample_docids = statusdb.post_view(
        db="charon",
        ddoc="sample",
        view="sampleid",
        start_key=[pid, "A"],
        end_key=[pid, "ZZ"]
        ).get_result()["rows"]
    for row in sample_docids:
        ids.append(row["id"])
    prep_docids = statusdb.post_view(
        db="charon",
        ddoc="libprep",
        view="libprepid",
        start_key=[pid, "A", "A"],
        end_key=[pid, "ZZ", "ZZ"]
        ).get_result()["rows"]
    for row in prep_docids:
        ids.append(row["id"])
    seqrundoc_ids = statusdb.post_view(
        db="charon",
        ddoc="seqrun",
        view="seqrunid",
        start_key=[pid, "A", "A", "A"],
        end_key=[pid, "ZZ", "ZZ", "ZZ"]
        ).get_result()["rows"]
    for row in seqrundoc_ids:
        ids.append(row["id"])

    for i in ids:
        doc = statusdb.get_document(db="charon", doc_id=i).get_result()
        try:
            docd = statusdb_dev.get_document(db="charon", doc_id=i).get_result()
        except ApiException:
            docd = {}
            for key in list(doc.keys()):
                if key != '_rev':
                    docd[key] = doc[key]
        statusdb_dev.post_document(db="charon", document=docd).get_result()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="project", required=True)
    parser.add_argument("-c", dest="conf", default="{0}/conf/LIMS2DB/post_process.yaml".format(os.environ["HOME"]))
    args = parser.parse_args()
    main(args)
