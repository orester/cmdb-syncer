"""
Host Model
"""
# pylint: disable=no-member, too-few-public-methods, too-many-instance-attributes
import datetime
from mongoengine.errors import DoesNotExist
from application import db, app

class HostError(Exception):
    """
    Errors related to host updates or creation
    """

class Label(db.EmbeddedDocument):
    """ Label Object (CMK Style)"""
    key = db.StringField()
    value = db.StringField()

class Target(db.EmbeddedDocument):
    """
    Target Stats
    """
    target_account_id = db.StringField()
    target_account_name = db.StringField()
    last_update = db.DateTimeField()

class Host(db.Document):
    """
    Host
    """
    hostname = db.StringField(required=True, unique=True)
    labels = db.ListField(db.EmbeddedDocumentField(Label))
    invenentory = db.DictField()

    force_update = db.BooleanField(default=False)

    source_account_id = db.StringField()
    source_account_name = db.StringField()

    available = db.BooleanField()

    last_seen = db.DateTimeField() # @deprecated
    last_update_on_target = db.DateTimeField() # @deprecated

    last_export = db.DateTimeField()

    last_import_seen = db.DateTimeField()
    last_import_sync = db.DateTimeField()

    last_import_seen = db.DateTimeField()
    last_import_sync = db.DateTimeField()


    folder = db.StringField()

    export_problem = False

    log = db.ListField(db.StringField())


    meta = {
        'strict': False,
    }


    @staticmethod
    def get_host(hostname):
        """
        Return existing Host or
        create a object and return it
        """
        try:
            return Host.objects.get(hostname=hostname)
        except DoesNotExist:
            pass

        new_host = Host()
        new_host.hostname = hostname
        return new_host


    def set_export_problem(self, message):
        """
        Mark Host as Export problem
        """
        self.export_problem = True
        self.add_log(message)
        self.save()

    def lock_to_folder(self, folder_name):
        """
        Lock System to given Folder
        Or remove it folder is False
        """
        if not folder_name:
            self.folder = None
        else:
            self.folder = folder_name
        self.save()

    def get_folder(self):
        """ Returns Folder if System is locked to one, else False """
        if self.folder:
            return self.folder
        return False

    def replace_label(self, key, value):
        """
        Replace given Label name with value
        """
        hit = False
        for label in self.labels:
            if label.key == key:
                label.value = value
                hit = True
        if not hit:
            label = Label()
            label.key = key
            label.value = value
            self.labels.append(label)

    def set_labels(self, label_dict):
        """
        Overwrites the Labels on this object
        """
        labels = []
        for key, value in label_dict.items():
            if not value:
                continue
            label = Label()
            label.key = key
            label.value = value
            labels.append(label)
        self.labels = labels

    def get_labels(self):
        """
        Return Labels
        in Dict Format
        """
        return dict({x.key:x.value for x in self.labels})

    def get_inventory(self):
        """
        Return Hosts Inventory Data.
        Used eg. for Ansible
        """
        return self.invenentory

    def add_log(self, entry):
        """
        Add a new Entry to the Host log
        """
        entries = self.log[:app.config['HOST_LOG_LENGTH']-1]
        date = datetime.datetime.now().strftime(app.config['TIME_STAMP_FORMAT'])
        self.log = [f"{date} {entry}"] + entries

    def set_account(self, account_id, account_name):
        """
        Set account Information
        """
        if self.source_account_id and self.source_account_id != account_id:
            raise HostError(f"Host {self.hostname} already importet by source {self.source_name}")
        self.source_account_id = account_id
        self.source_account_name = account_name


    #@deprecated
    def set_source_update(self):
        """
        Replaced by set_import_sync()
        """
        print("Deprecated: Please migrate 'set_source_update() 1to1 to set_import_seen. Also note new set_import_sync whicht you can use to differ in more detail")
        self.available = True
        self.last_seen = datetime.datetime.now()
        # Prepare Field already for the future:
        self.last_import_sync = datetime.datetime.now()

    def set_import_sync(self):
        """
        Called always when we Update data
        to this object on import
        """
        self.available = True
        self.last_import_sync = datetime.datetime.now()

    def set_import_seen(self):
        """
        Call when seen on the import source,
        even if no update happens
        """
        self.available = True
        self.last_import_seen = datetime.datetime.now()


    def set_source_not_found(self):
        """
        When not found anymore on source,
        this will be set
        """
        self.available = False
        self.add_log("Not found on Source anymore")

    #@deprecated support
    def set_target_update(self):
        """
        Mark that host was updated on Target
        """
        print("Deprecated: Please migrate 'set_target_update() 1to1 to set_export_sync()")
        self.last_update_on_target = datetime.datetime.now()
        self.last_export = datetime.datetime.now()
        self.save()


    def set_export_sync(self):
        """
        Mark that host was updated on Export Target
        """
        self.last_export = datetime.datetime.now()
        self.save()

    #@deprecated support
    def need_sync(self, hours=24):
        """
        Replace by: Need Import Sync
        just need sync can be missleading
        """
        print("Deprecated: Please migrate 'need_sync() 1to1 to need_import_sync")
        if not self.available:
            return True
        timediff = datetime.datetime.now() - self.last_seen
        if divmod(timediff.total_seconds(), 3600)[0] > hours:
            return True
        return False

    def need_import_sync(self, hours=24):
        """
        Check if the host needs to be synced
        from the source
        """
        print("Deprecated: Please migrate 'need_sync() 1to1 to need_import_sync()")
        if not self.available:
            return True

        last_sync = self.last_import_sync
        # deprecated support
        if not last_sync:
            last_sync = self.last_seen
        timediff = datetime.datetime.now() - last_sync
        if divmod(timediff.total_seconds(), 3600)[0] > hours:
            return True
        return False

    def need_import_sync(self, hours=24):
        """
        Check if the host needs to be synced
        from the import source
        """
        if not self.available:
            return True

        last_sync = self.last_import_sync
        # deprecated support
        if not last_sync:
            last_sync = self.last_seen
        timediff = datetime.datetime.now() - last_sync
        if divmod(timediff.total_seconds(), 3600)[0] > hours:
            return True
        return False


    def need_update(self, hours=24*7):
        """
        Check if we need to Update this host
        on the target
        """
        # deprecated support
        last_export = self.last_export
        if not last_export:
            last_export = self.last_update_on_target

        if not last_export:
            return True
        if self.force_update:
            self.force_update = False
            self.save()
            return True
        timediff = datetime.datetime.now() - self.last_export
        if divmod(timediff.total_seconds(), 3600)[0] > hours:
            return True
        return False
