// vector can only store same type
// but enum can tackle it

fn construct() {
    let v: Vec<i32> = Vec::new();
    let mut v = vec![1, 2, 3];
}

fn vpush() {
    let mut v = Vec::new();
    v.push(5);
    v.push(1);
    v.push(6);
    println!("{:?}", v);
}

// like get in Python
fn vget() {
    let v = vec![1, 2, 3, 4, 5];
    let third: &i32 = &v[2];
    let third: Option<&i32> = v.get(2);
    match third {
        Some(v) => println!("{}", v),
        _ => (),
    }
}

fn multitype() {
    #[derive(Debug)]
    enum SpreadSheetCell {
        Int(i32),
        Float(f64),
        Text(String),
    }
    let row = vec![
        SpreadSheetCell::Int(3),
        SpreadSheetCell::Text(String::from("blue")),
        SpreadSheetCell::Float(10.12),
    ];

    for i in row.iter() {
        println!("{:?}", i);
    }
}

fn main() {
    construct();
    vpush();
    vget();
    multitype();
}