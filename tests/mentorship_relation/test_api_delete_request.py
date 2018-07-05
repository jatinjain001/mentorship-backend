import json
import unittest
from datetime import datetime, timedelta

from app.database.sqlalchemy_extension import db
from app.database.models.mentorship_relation import MentorshipRelationModel
from app.utils.enum_utils import MentorshipRelationState
from app.database.models.user import UserModel
from tests.base_test_case import BaseTestCase
from tests.test_data import user1, user2
from tests.test_utils import get_test_request_header


class TestDeleteMentorshipRequestApi(BaseTestCase):

    # Setup consists of adding 2 users into the database
    # User 1 is the mentorship relation requester = action user
    # User 2 is the receiver
    def setUp(self):
        super(TestDeleteMentorshipRequestApi, self).setUp()

        self.first_user = UserModel(
            name=user1['name'],
            email=user1['email'],
            username=user1['username'],
            password=user1['password'],
            terms_and_conditions_checked=user1['terms_and_conditions_checked']
        )
        self.second_user = UserModel(
            name=user2['name'],
            email=user2['email'],
            username=user2['username'],
            password=user2['password'],
            terms_and_conditions_checked=user2['terms_and_conditions_checked']
        )

        # making sure both are available to be mentor or mentee
        self.first_user.need_mentoring = True
        self.first_user.available_to_mentor = True
        self.second_user.need_mentoring = True
        self.second_user.available_to_mentor = True

        self.notes_example = 'description of a good mentorship relation'

        self.now_datetime = datetime.now()
        self.end_date_example = self.now_datetime + timedelta(weeks=5)

        db.session.add(self.first_user)
        db.session.add(self.second_user)
        db.session.commit()

        # create new mentorship relation

        self.mentorship_relation = MentorshipRelationModel(
            action_user_id=self.first_user.id,
            mentor_user=self.first_user,
            mentee_user=self.second_user,
            creation_date=self.now_datetime.timestamp(),
            end_date=self.end_date_example.timestamp(),
            state=MentorshipRelationState.PENDING,
            notes=self.notes_example
        )

        db.session.add(self.mentorship_relation)
        db.session.commit()

    def test_sender_delete_mentorship_request(self):
        request_id = self.mentorship_relation.id

        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)
        self.assertIsNotNone(MentorshipRelationModel.query.filter_by(id=request_id).first())

        with self.client:
            response = self.client.delete('/mentorship_relation/%s' % request_id,
                                          headers=get_test_request_header(self.first_user.id))

        self.assertEqual(200, response.status_code)
        self.assertEqual({'message': 'Mentorship relation was deleted successfully.'},
                         json.loads(response.data))
        self.assertIsNone(MentorshipRelationModel.query.filter_by(id=request_id).first())

    def test_receiver_delete_mentorship_request(self):
        request_id = self.mentorship_relation.id

        self.assertEqual(MentorshipRelationState.PENDING, self.mentorship_relation.state)
        self.assertIsNotNone(MentorshipRelationModel.query.filter_by(id=request_id).first())

        with self.client:
            response = self.client.delete('/mentorship_relation/%s' % request_id,
                                          headers=get_test_request_header(self.second_user.id))

        self.assertEqual(400, response.status_code)
        self.assertEqual({'message': 'You cannot delete a mentorship request that you did not create.'},
                         json.loads(response.data))
        self.assertIsNotNone(MentorshipRelationModel.query.filter_by(id=request_id).first())


if __name__ == "__main__":
    unittest.main()
