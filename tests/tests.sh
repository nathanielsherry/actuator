#!/bin/bash


function test() {
	echo "-= Testing $1 =-"
	./$1.act | diff $1.out -
	if [ $? -eq "1" ]; then
		echo "   [FAILED]"
	else
		echo "   [  OK  ]"
	fi
	echo ""
}

test "echo"
test "inflows"
test "vars"
test "varval"
test "namespace"
test "lst"
test "subflows"
test "flowref"
test "autoinflow"
