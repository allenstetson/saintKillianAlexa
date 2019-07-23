import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

class KillianDataManager(object):
    def __init__(self):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name="us-east-1",
            endpoint_url="http://dynamodb.us-east-1.amazonaws.com"
        )
        self.dbTable = self.dynamodb.Table("StKillian")

    def getCalendarEvents(self, monthOffset=0):
        msg = "Attempting to retrieve calendar events from db"
        logger.info(msg)

        now = datetime.datetime.now()
        month = now.month
        month += monthOffset
        if month > 12:
            month = month - 12
        elif month < 1:
            month = month + 12

        item = None
        try:
            fe = Key("eventCategory").eq("calendar")
            response = self.dbTable.scan(
                FilterExpression=fe,
            )
            logger.info("response: {}".format(response))
            if response['Count'] == 0:
                logger.info("No items found for query.")
                return []
            return response['Items']

        except ClientError as e:
            logger.info("get_item for mass times failed.")
            logger.error(e.response['Error']['Message'])
            return []


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
                UpdateExpression="set lastToken=:o, lastTrack=:k, offsetInMilliseconds=:f",
                ExpressionAttributeValues={
                    ":o": dbEntry.get("lastToken", ""),
                    ":k": dbEntry.get("lastTrack", ""),
                    ":f": dbEntry.get("offsetInMilliseconds", 0)
                },
                ReturnValues="UPDATED_NEW"
            )
            return True
        except ClientError as e:
            logger.info("ClientError received!")
            logger.error(e.response["Error"]["Message"])
            return False
