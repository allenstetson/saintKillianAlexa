import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from botocore.exceptions import ClientError
import boto3

class KillianDataManager(object):
    def __init__(self):
        dynamodb = boto3.resource(
            "dynamodb",
            region_name="us-east-1",
            endpoint_url="http://dynamodb.us-east-1.amazonaws.com"
        )
        self.dbTable = dynamodb.Table("StKillian")

    def getMassTimes(self, dayEnum):
        msg = "Attempting to retrieve mass times for {} from db"
        msg = msg.format(dayEnum)
        logger.info(msg)

        namespace = "event:mass:daily:{}".format(dayEnum)
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': namespace}
            )
            if not 'Item' in response:
                return None
            item = response['Item']
        except ClientError as e:
            logger.info("get_item for mass times failed.")
            logger.error(e.response['Error']['Message'])
            return None

        times = list()
        for massString in item['eventTimes']:
            if len(massString.split(",")) == 2:
                hourNum, minNum = massString.split(",")
                language = "english"
            else:
                hourNum, minNum, language = massString.split(",")

            times.append((datetime.time(int(hourNum), int(minNum)), language))
        times = sorted(times, key=lambda x: x[0].hour)
        return times

    def getParishOfficePhoneNumber(self):
        msg = "Attempting to retrieve parish office phone number from db"
        logger.info(msg)

        namespace = "info:office:phone"
        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': namespace}
            )
            if not 'Item' in response:
                return None
            item = response['Item']
        except ClientError as e:
            logger.info("get_item for parish office phone failed.")
            logger.error(e.response['Error']['Message'])
            return None

        return item['phoneNumber']

    def getUserDatabaseEntry(self, userId):
        msg = "Attempting to find user entry for userId..."
        logger.info(msg)

        item = None
        try:
            response = self.dbTable.get_item(
                TableName="StKillian",
                Key={'namespace': userId}
            )
            if not "Item" in response:
                logger.info("New user!")
                return {}
            item = response['Item']
        except ClientError as e:
            logger.info("get_item for userId failed.")
            logger.error(e.response['Error']['Message'])
            return None

        return item

    def updateUserDatabaseEntry(self, userId, dbEntry):
        msg = "Attempting to write user data..."
        logger.info(msg)

        try:
            self.dbTable.update_item(
                TableName="StKillian",
                Key={"namespace": userId},
                UpdateExpression="set lastToken=:o, lastTrack=:k",
                ExpressionAttributeValues={
                    ":o": dbEntry.get("lastToken", ""),
                    ":k": dbEntry.get("lastTrack", "")
                },
                ReturnValues="UPDATED_NEW"
            )
            return True
        except ClientError as e:
            logger.info("ClientError received!")
            logger.error(e.response["Error"]["Message"])
            return False
