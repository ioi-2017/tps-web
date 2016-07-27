from django.test import TestCase
from django.utils import timezone

from version_control.tests.models import Question, Choice, Person, Student, Group, Membership, A, B, C


def get_information_list(object_list):
    information_list = []
    for object in object_list:
        information_list.append((object.pk, object.__module__ + "." + object.__class__.__name__))
    information_list.sort()
    return information_list


class VersionControlTests(TestCase):
    def test_get_all_neighbor_objects(self):
        question = Question(question_text='question1', pub_date=timezone.now())
        question.save()
        choice = question.choice_set.create(choice_text='a', votes=0)
        c = Choice(question=question, choice_text='b', votes=0)
        c.save()
        choice.save()
        person = Person()
        person.save()
        person.questions.add(question)
        test_list = [(question.pk, question.__module__ + "." + question.__class__.__name__)]
        self.assertEqual(get_information_list(person.get_all_neighbor_objects()), test_list)
        self.assertEqual(get_information_list(c.get_all_neighbor_objects()), test_list)
        test_list.clear()
        test_list = [(choice.pk, choice.__module__ + "." + choice.__class__.__name__), (c.pk, c.__module__ + "." + c.__class__.__name__), (person.pk, person.__module__ + "." + person.__class__.__name__)]
        test_list.sort()
        self.assertEqual(get_information_list(question.get_all_neighbor_objects()), test_list)

    def test_get_all_related_objects(self):
        question = Question(question_text='question1', pub_date=timezone.now())
        q1 = Question(question_text='q1', pub_date=timezone.now())
        q1.save()
        question.save()
        choice = question.choice_set.create(choice_text='a', votes=0)
        c = Choice(question=question, choice_text='b', votes=0)
        c.save()
        choice.save()
        c1 = q1.choice_set.create(choice_text='a', votes=0)
        c1.save()
        person = Person()
        person.save()
        person.questions.add(question)
        test_list = [(q1.pk, q1.__module__+ "." + q1.__class__.__name__), (c1.pk, c1.__module__ + "." + c1.__class__.__name__)]
        test_list.sort()
        self.assertEqual(get_information_list(q1.get_all_related_object()), test_list)
        self.assertEqual(get_information_list(c1.get_all_related_object()), test_list)
        test_list.clear()
        test_list = [(question.pk, question.__module__ + "." + question.__class__.__name__), (c.pk, c.__module__ + "." + c.__class__.__name__), (choice.pk, choice.__module__ + "." + choice.__class__.__name__),
                     (person.pk, person.__module__ + "." + person.__class__.__name__)]
        test_list.sort()
        self.assertEqual(get_information_list(question.get_all_related_object()), test_list)
        self.assertEqual(get_information_list(c.get_all_related_object()), test_list)
        self.assertEqual(get_information_list(choice.get_all_related_object()), test_list)
        self.assertEqual(get_information_list(person.get_all_related_object()), test_list)
        self.assertNotEqual(get_information_list(q1.get_all_related_object()), test_list)

    def test_get_all_related_objects_with_circular_relation(self):
        a_object = A()
        b_object = B()
        c_object = C()
        a_object.save()
        b_object.save()
        c_object.save()
        a_object.b.add(b_object)
        b_object.c.add(c_object)
        c_object.a.add(a_object)
        test_list = [(b_object.pk, b_object.__module__ + "." + b_object.__class__.__name__), (c_object.pk, c_object.__module__ + "." + c_object.__class__.__name__), (a_object.pk, a_object.__module__ + "." + a_object.__class__.__name__)]
        test_list.sort()
        self.assertEqual(get_information_list(a_object.get_all_related_object()), test_list)
        self.assertEqual(get_information_list(b_object.get_all_related_object()), test_list)
        self.assertEqual(get_information_list(c_object.get_all_related_object()), test_list)

    def test_clone_with_one_object(self):
        question = Question(question_text='a', pub_date=timezone.now())
        question.save()
        q = question.clone([])
        self.assertNotEqual(q.pk, question.pk)
        self.assertEqual(q.question_text, question.question_text)
        self.assertEqual(q.pub_date, question.pub_date)

    def test_clone_with_foreign_key(self):
        question = Question(question_text='a', pub_date=timezone.now())
        question.save()
        choice = Choice(question=question, choice_text='c', votes=0)
        choice.save()
        c = choice.clone([])
        self.assertNotEqual(choice.id, c.id)
        self.assertNotEqual(choice.question.id, c.question.id)
        self.assertEqual(choice.question.question_text, c.question.question_text)
        q = question.clone([])
        self.assertNotEqual(q.id, question.id)
        self.assertNotEqual(question.choice_set.get(choice_text='c').pk, q.choice_set.get(choice_text='c').pk)

    def test_clone_with_ignore_list(self):
        question = Question(question_text='a', pub_date=timezone.now())
        question.save()
        choice = Choice(question=question, choice_text='c', votes=0)
        choice.save()
        c = choice.clone([type(question)])
        self.assertNotEqual(choice.id, c.id)
        self.assertEqual(choice.question.id, c.question.id)

    def test_clone_with_many_to_many_field(self):
        question = Question(question_text='question1', pub_date=timezone.now())
        question.save()
        person = Person()
        person.save()
        person.questions.add(question)
        p = person.clone([])
        self.assertNotEqual(person.id, p.id)
        self.assertNotEqual(person.questions.get(question_text='question1').id,
                            p.questions.get(question_text='question1').id)

    def test_clone_many_to_many_field_with_repeated_instance(self):
        question = Question(question_text='question1', pub_date=timezone.now())
        question.save()
        person = Person()
        person.save()
        person.questions.add(question)
        person.questions.add(question)
        p = person.clone([])
        self.assertEqual(person.questions.all().count(), p.questions.all().count())

    def test_clone_with_through_field(self):
        student = Student(name='Ali')
        group = Group(name='ACM')
        student.save()
        group.save()
        membership = Membership(student=student, group=group)
        membership.save()
        g = group.clone([])
        self.assertNotEqual(g.id, group.id)
        self.assertNotEqual(group.members.get(name='Ali').id, g.members.get(name='Ali').id)
        s = student.clone([])
        self.assertNotEqual(s.id, student.id)
        self.assertNotEqual(student.group_set.get(name='ACM').id, s.group_set.get(name='ACM').id)

    def test_clone_many_to_many_field_with_through_field_and_repeated_instance(self):
        student = Student(name='Ali')
        group = Group(name='ACM')
        student.save()
        group.save()
        membership1 = Membership(student=student, group=group)
        membership1.save()
        membership2 = Membership(student=student, group=group)
        membership2.save()
        g = group.clone([])
        self.assertEqual(g.members.all().count(), group.members.all().count())
        s = student.clone([])
        self.assertEqual(s.group_set.all().count(),  student.group_set.all().count())