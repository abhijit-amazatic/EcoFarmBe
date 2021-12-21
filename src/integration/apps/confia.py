"""
Confia utility.
"""
import json
import time
from requests import request
import uuid
import hashlib
from datetime import (datetime,)
from core.celery import (app,)
from celery.task import periodic_task
from celery.schedules import crontab
from core.settings import (CONFIA_ACCESS_ID,
                           CONFIA_ACCESS_KEY,
                           CONFIA_ACCESS_SECRET,
                           CONFIA_API_BASE_URL,)

def get_confia_headers():
    """
    Return headers.Modify if needed.
    """
    return {
        'Content-Type': 'application/json',
        'accessId':CONFIA_ACCESS_ID,
        'accessKey':CONFIA_ACCESS_KEY
    }

def get_sha_hash_fingerprint(payer_id,recipient_id,amount,partner_transaction_id):
    """
    Create shaHash Fingerprint.
    """
    sha_str= "%s-%s-%s-%s-%s" %(payer_id,recipient_id,str(amount),CONFIA_ACCESS_SECRET,partner_transaction_id)
    fingerprint = hashlib.sha256(sha_str.encode())
    return fingerprint.hexdigest()
    
@app.task(queue="urgent")
def initiate_b2b_transaction(payer_id,recipient_id,amount,partner_transaction_id=None):
    """
    Initiate transactions.(Add partner_transaction_id in specific format if needed).

    Extra Payload can be added as:
    {
	'licenseManifestId': 'string',
	'purchasedItems': [{
		'cultivationCategory': 'FLOWERS',
		'cultivationTaxAmount': 1.95,
		'description': 'string',
		'discount': 1.95
	}],
	'scheduledPaymentDate': '2021-12-16'
    }
    Returns:
    {
    "created": "2021-12-16T18:15:05.316Z",
    "status": "CANCELLED_BY_AUTHORITY",
    "transactionId": "string"
    }
    """
    confia_url = CONFIA_API_BASE_URL+'v1/transaction/b2b'
    headers = get_confia_headers()
    partner_transaction_id = str(uuid.uuid1())
    payload = {
	'partnerTransactionId': partner_transaction_id,
	'payorId': payer_id,
	'recipientId':recipient_id,
	'shaHash':get_sha_hash_fingerprint(payer_id,recipient_id,amount,partner_transaction_id),
	'totalAmount': amount
    }
    try:
        response = request("POST",confia_url, headers=headers,data=json.dumps(payload))
    except Exception as e:
        print('exception', e)
        return {'error': f'Error while creating b2b transaction-{e}'}
    return response.json() #{'status_code': response.status_code, 'response': response.json()}
    
def search_transaction(transaction_id):
    """
    Search for business payments.
    Note:
       - 'memberId'(payer ID) should be present in request if transaction id is empty.(Either of them should be there)
       - We can also search by 'otherMemberId'.Update params according to need.
    """
    data = {'transactionId':transaction_id} #{'memberId': payer_id}
    response = request("GET",CONFIA_API_BASE_URL+'v1/transaction',headers=get_confia_headers(),params=data)
    return response.json()

def get_transaction_by_partner_id(external_id):
    """
    get payments by External partner transaction id
    """
    response = request("GET",CONFIA_API_BASE_URL+'v1/external/'+ str(external_id),headers=get_confia_headers())
    return response.json()

def delete_transaction(transaction_id,reason):
    """
    Cancel a business payment between Confia members (B2B payment).
    """
    try:
        response = request("DELETE",CONFIA_API_BASE_URL+'v1/transaction/b2b',
                           headers=get_confia_headers(),
                           data=json.dumps({
                               'reason': reason,
                               'transactionId': transaction_id 
                           }))
    except Exception as e:
        return {'error': f'Error while deleting b2b transaction-{e}'}
    return response.json() 

@app.task(queue="urgent")
def initiate_b2b_refund(partner_transaction_id,reason,refund_amount,sha_hash,transaction_id):
    
    """
    Issues a refund from a Confia Member to either a Consumer or other Member.
    This can be used for both retail and b2b payments.Multiple refund requests can be made per transaction,
    but the sum of those requests cannot exceed the total transaction amount.
    """

    try:
        payload = {
            "partnerTransactionId": partner_transaction_id,
            "reason":reason,
            "refundAmount": int(refund_amount),
            "shaHash":sha_hash,
            "transactionId":transaction_id
        }
        response = request("POST",CONFIA_API_BASE_URL+'v1/transaction/refund',
                           headers=get_confia_headers(),
                           data=json.dumps(payload))
    except Exception as e:
        return {'error': f'Error while b2b refund-{e}'}
    return response.json()


def search_member(member_id):
    """
    Search for members.
    """
    data = {'memberId':member_id}
    response = request("GET",CONFIA_API_BASE_URL+'v1/member',headers=get_confia_headers(),params=data)
    return response.json()

def search_merchant(member_id):
    """
    Search for merchants.
    """
    response = request("GET",CONFIA_API_BASE_URL+'v1/member/merchant',headers=get_confia_headers(),params={'memberId':member_id})
    return response.json()
    




        
    
    
    




