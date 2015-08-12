

def Task(Base):

    pid = Column(types.Integer, nullable=False, default=-1)
    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    working_path = Column(types.String(128), nullable=False, default='')

