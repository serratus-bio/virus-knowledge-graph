from queries import pyg_queries


def run(args):
    data = pyg_queries.create_pyg_graph()
    train_data, val_data, test_data = pyg_queries.split_data(data)
    train_loader = pyg_queries.get_train_loader(train_data)
    model = pyg_queries.get_model(data)
    pyg_queries.train(model, train_loader)
    val_loader = pyg_queries.get_val_loader(val_data)
    pyg_queries.eval(model, val_loader)
